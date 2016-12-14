# Некоторые идеи взяты отсюда: https://github.com/bfirsh/django-ordered-model/blob/master/ordered_model/models.py

from django.db import models
from django.db.models import Max, F, QuerySet
from django.utils.translation import ugettext_lazy as _


class OrderedModel(models.Model):
    """
    Абстрактная базовая модель, предоставляющая отдельное поле для упорядочивания и методы для работы с очерёдностью
    """

    class Meta:
        ordering = ['order']
        abstract = True
        order_domain_field = ''

    MIN_ORDER_VALUE = 0

    order = models.PositiveIntegerField(
        db_index=True,
        editable=False,
        verbose_name=_('порядок')
    )

    def get_order_domain_value(self):
        """
        Возвращает значение поля, по которому происходит разделение на области упорядочивания

        :return: Значение поля, по которому происходит разделение на области упорядочивания
        """
        return getattr(self, self.Meta.order_domain_field)

    def get_order_domain_qs(self, qs: QuerySet=None) -> QuerySet:
        """
        Возвращает QuerySet, сформированный с учётом разделения на области упорядочивания

        :param qs: Базовый QuerySet для модели. Если не указан - используется objects.all()
        :return: QuerySet, сформированный с учётом разделения на области упорядочивания
        """
        qs = qs if qs is not None else type(self).objects.all()
        if self.Meta.order_domain_field:
            qs = qs.filter((self.Meta.order_domain_field, self.get_order_domain_value()))
        return qs

    def _get_max_order(self):
        """
        Возвращает максимальное значение поля, определяющего порядок

        :return: Максимальное значение поля, определяющего порядок
        """
        return self.get_order_domain_qs().aggregate(Max('order')).get('order__max')

    def _insert_new(self):
        """
        Определяет значение порядка для сохраняемого экземпляра модели, а также сдвигает всех на одно место вперёд

        :return: None
        """
        max_order = self._get_max_order()
        if self.order is None:
            # Нужно сунуть в конец
            self.order = self.MIN_ORDER_VALUE if max_order is None else max_order + 1
        else:
            if max_order is None:
                # если ещё нет ни одного объекта
                self.order = self.MIN_ORDER_VALUE
            elif self.order > max_order + 1:
                # выехал за пределы порядка - ничего двигать не надо
                self.order = max_order + 1
            else:
                # нужно подвинуть вправо, что справа от нового места
                self.get_order_domain_qs(type(self).objects.select_for_update().filter(
                    order__gte=self.order
                )).update(order=F('order') + 1)

    def save(self, skip_reorder: bool=False, *args, **kwargs) -> None:
        """
        Сохраняет экземпляр модели со сдвигом порядка, если необходимо

        Параметр skip_reorder позволяет принудительно отменить все корректировки порядка в связи с добавлением нового
        элемента. Т.е. при этом возможна такая ситуация, что несколько экземпляров в одной области упорядочивания будут
        иметь одинаковые значения порядка. Это позволяет сократить количество операций с БД при внесении изменений,
        но должно быть исправлено позднее с помощью метода order_check.

        :param skip_reorder: Если True - отменяет все корректировки порядка у других экземпляров, сохраняя как есть
        :return: None
        """
        if not skip_reorder:
            if self.order is not None and self.order < self.MIN_ORDER_VALUE:
                self.order = self.MIN_ORDER_VALUE
            if self.pk is not None:
                # Если уже установлен первичный ключ, то, возможно - это редактирование существующего объекта
                try:
                    old_order = type(self).objects.filter(pk=self.pk).values_list('order', flat=True)[0]
                except IndexError:
                    old_order = None
                if old_order is None:
                    # Значит - это всё-таки добавление нового, а pk взялся непонятно откуда
                    self._insert_new()
                else:
                    # Значит - обновление существующего
                    if self.order is None:
                        # Нужно сунуть в конец
                        max_order = self._get_max_order()
                        if old_order < max_order:
                            # нужно двигать назад всё, что справа от старого места
                            self.get_order_domain_qs(type(self).objects.select_for_update().filter(
                                order__gt=old_order
                            )).update(order=F('order') - 1)
                        self.order = max_order
                    else:
                        # Нужно разобраться - куда кого девать
                        if self.order > old_order:
                            # если сдвиг вправо
                            max_order = self._get_max_order()
                            if self.order > max_order:
                                # выехал за пределы порядка
                                self.order = max_order
                            # двигаем всё, что находится между старым и новым местом влево
                            self.get_order_domain_qs(type(self).objects.select_for_update().filter(
                                order__gt=old_order,
                                order__lte=self.order
                            )).update(order=F('order') - 1)
                        elif self.order < old_order:
                            # если сдвиг влево - двигаем всё, что находится между старым и новым местом вправо
                            self.get_order_domain_qs(type(self).objects.select_for_update().filter(
                                order__gte=self.order,
                                order__lt=old_order
                            )).update(order=F('order') + 1)
            else:
                # Это добавление нового объекта
                self._insert_new()
        super().save(*args, **kwargs)

    def delete(self, skip_reorder: bool=False, *args, **kwargs) -> None:
        """
        Удаляет экземпляр модели со сдвигом порядка, если необходимо

        Параметр skip_reorder работает аналогично методу save

        :param skip_reorder: Если True - отменяет все корректировки порядка у других экземпляров, удаляя как есть
        :param args:
        :param kwargs:
        :return: None
        """
        if not skip_reorder:
            self.get_order_domain_qs(type(self).objects.filter(order__gt=self.order)).update(order=F('order') - 1)
        super().delete(*args, **kwargs)

    def order_swap(self, swap_with) -> None:
        """
        Меняет местами (в отношении порядка) два экземпляра одной модели - текущий и переданный в качестве аргумента

        :param swap_with: Экземпляр модели, с которым текущий меняется местами
        :return: None
        """
        if type(swap_with) != type(self):
            raise ValueError(
                _('Можно менять местами только объекты одного класса, предоставлены: '
                  '%(self_class)s, %(other_class)s.') % {'self_class': type(self), 'other_class': type(swap_with)}
            )
        if self.pk is None or swap_with.pk is None:
            raise ValueError(_('Перед тем, как менять объекты местами, их необходимо сохранить.'))
        if self.get_order_domain_qs(
                type(self).objects.select_for_update().filter(pk__in=[self.pk, swap_with.pk])
        ).count() != 2:
            raise ValueError(_('Перед тем, как менять объекты местами, их необходимо сохранить.'))
        if self.Meta.order_domain_field:
            if self.get_order_domain_value() != swap_with.get_order_domain_value():
                raise ValueError(_('Объекты должны принадлежать к одной области упорядочивания.'))
        self.order, swap_with.order = swap_with.order, self.order
        self.save(skip_reorder=True)
        swap_with.save(skip_reorder=True)

    @classmethod
    def order_check(cls) -> None:
        """
        Проверяет значения поля порядка для всех записей класса в БД, при необходимости - исправляет все несоответствия

        :return: None
        """
        if not cls.order_domain_field:
            order_list = list(cls.objects.order_by('order', '-id').values_list('id', 'order'))
            if not order_list or len(order_list) == 1:
                return
            for k, v in enumerate(order_list):
                if k + cls.MIN_ORDER_VALUE != v[1]:
                    cls.objects.filter(pk=v[0]).update(order=k + cls.MIN_ORDER_VALUE)
        else:
            order_domain_values = list(
                cls.objects.order_by(cls.order_domain_field).distinct(cls.order_domain_field).values_list(
                    cls.order_domain_field, flat=True)
            )
            for odv in order_domain_values:
                order_list = list(
                    cls.objects.filter((cls.order_domain_field, odv)).order_by('order', '-id').values_list('id', 'order')
                )
                if not order_list or len(order_list) == 1:
                    continue
                for k, v in enumerate(order_list):
                    if k + cls.MIN_ORDER_VALUE != v[1]:
                        cls.objects.filter(pk=v[0]).update(order=k + cls.MIN_ORDER_VALUE)
