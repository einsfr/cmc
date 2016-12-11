"""
Пакет с настройками проекта

Обеспечивает возможность разделения настроек на части, поддерживает явную автоматическую загрузку конфигураций
по-умолчанию из установленных приложений. Предполагаемый принцип работы - импорт настроек в общее пространство модуля
settings, используемого Django по-умолчанию.
"""
import importlib
import re

__all__ = ['import_settings', ]

SIMP_CONF_ROOT = str(__name__)
SIMP_APP_SETTINGS_MODULE = 'default_settings'


def import_settings(import_to: dict, modules: list, installed_apps: list = None, merge: tuple = ()) -> None:
    """
    Импортирует настройки из модулей, описанных в modules в словарь import_to

    Идентификаторы импортируемых модулей - это:
    - модули Python, расположенные в корневой папке настроек (SIMP_CONF_ROOT). Записываются так же, как при обычном
      импорте: common или com.mon
    - регулярные выражения для загруженных приложений (installed_apps). Такие идентификаторы начинаются с @. Тут следует
      отметить, что работать это будет только тогда, когда приложение загружается по полному пути к своему модулю.
      Использование подклассов AppConfig на данный момент делает использование этого загрузчика невозможным.
    Также можно отметить любой идентификатор - как модуль, так и регулярное выражение для приложения - значком *.
    Это делает данный идентификатор не обязательным к загрузке - например, если неизвестно, будет он использоваться
    или нет.

    :param import_to: Словарь, к которому идёт присоединение
    :param modules: Список с идентификаторами импортируемых модулей
    :param installed_apps: Список установленных приложений
    :param merge: Кортеж, содержащий список параметров, подлежащих слиянию вместо замены
    :return: None
    """
    loaded_modules = []

    def _import_by_app_re(module_name: str, optional: bool) -> None:
        if not installed_apps:
            raise RuntimeError('Использовать @ для загрузки конфигураций из приложений можно только вместе с непустым '
                               'списком installed_apps.')
        import_list = [
            '{}.{}'.format(app, SIMP_APP_SETTINGS_MODULE) for app in installed_apps if re.match(module_name, app)
            ]
        if not import_list:
            return
        for i in import_list:
            _import_by_name(i, optional)

    def _import_by_name(module_name: str, optional: bool) -> None:
        if module_name in loaded_modules:
            return
        loaded_modules.append(module_name)
        try:
            imported_module = importlib.import_module(module_name)
        except ImportError:
            if optional:
                return
            else:
                raise
        module_settings = dict(
            [(s_name, getattr(imported_module, s_name)) for s_name in dir(imported_module) if s_name.isupper()]
        )
        _recursive_merge(module_settings, import_to, merge, True)

    for module_id in modules:
        if not module_id:
            raise ValueError('Идентификатор загружаемого модуля не может быть пустым.')
        mode_part = module_id[:2] if len(module_id) > 2 else module_id[:len(module_id) - 1]
        opt = '*' in mode_part
        app_re = '@' in mode_part
        module_id = module_id[opt + app_re:]
        if app_re:
            _import_by_app_re(module_id, opt)
        else:
            _import_by_name('{}.{}'.format(SIMP_CONF_ROOT, module_id), opt)


def _recursive_merge(from_dict: dict, to_dict: dict, merge: tuple = (), root: bool = True) -> None:
    """
    Осуществляет рекурсивное присоединение словаря from_dict к словарю to_dict

    Словари сливаются всегда. Другие типы могут сливаться (если они находятся на корневом уровне
    и указаны в кортеже merge) или замещаться.
    :param from_dict: Присоединяемый словарь
    :param to_dict: Словарь, к которому идёт присоединение
    :param merge: Кортеж, содержащий список параметров, подлежащих слиянию вместо замены
    :param root: Признак нахождения на корневом уровне
    :return: None
    """
    for (k, v) in from_dict.items():
        if k in to_dict:
            if isinstance(v, dict) and isinstance(to_dict[k], dict):
                _recursive_merge(v, to_dict[k], merge, False)
            elif root and k in merge:
                to_dict[k] = to_dict[k] + v
            else:
                to_dict[k] = v
        else:
            to_dict[k] = v