import bisect
import copy
import importlib
import inspect
import logging
import pkgutil
import sys
import time
import traceback
from threading import Event
from threading import RLock
from threading import Thread

from rwlock import RWLock

from iptv_proxy.exceptions import ProviderNotFoundError

logger = logging.getLogger(__name__)


class ProvidersController():
    __slots__ = []

    _active_providers = []
    _active_providers_lock = RWLock()
    _providers_executing_initialization = {}
    _providers_executing_termination = {}
    _providers_initialization_termination_lock = RLock()
    _providers_map_class = {}
    _providers_pending_initialization = {}
    _providers_pending_termination = {}
    _wait_event = Event()
    _stop_event = Event()

    @classmethod
    def _initialize_providers_map_class(cls):
        for module_info in pkgutil.walk_packages(path=sys.modules[__name__].__path__,
                                                 onerror=lambda x: None):
            if module_info.name != 'iptv_provider' and module_info.ispkg:
                map_module_path = '{0}.{1}.{2}'.format(__name__, module_info.name, 'map')

                importlib.import_module(map_module_path)

                for (class_name, class_) in inspect.getmembers(sys.modules[map_module_path], inspect.isclass):
                    if map_module_path in '{0}'.format(class_):
                        class_.initialize()

                        for (method_name, method) in inspect.getmembers(class_, inspect.ismethod):
                            if method_name == 'api_class':
                                cls._providers_map_class[method().__name__.lower()] = class_

    @classmethod
    def _run(cls):
        while True:
            with cls._providers_initialization_termination_lock:
                # <editor-fold desc="Cleanup providers that have completed termination">
                providers_executed_termination = []

                for provider_name in cls._providers_executing_termination:
                    if cls._providers_executing_termination[provider_name]['api_class_event'].is_set() and \
                            cls._providers_executing_termination[provider_name]['epg_class_event'].is_set():
                        providers_executed_termination.append(provider_name)

                for provider_name in providers_executed_termination:
                    del cls._providers_executing_termination[provider_name]
                # </editor-fold>

                # <editor-fold desc="Cleanup providers that have completed initialization">
                providers_executed_initialization = []

                for provider_name in cls._providers_executing_initialization:
                    if cls._providers_executing_initialization[provider_name]['api_class_event'].is_set() and \
                            cls._providers_executing_initialization[provider_name]['epg_class_event'].is_set():
                        providers_executed_initialization.append(provider_name)

                for provider_name in providers_executed_initialization:
                    del cls._providers_executing_initialization[provider_name]
                # </editor-fold>

                # <editor-fold desc="Terminate providers">
                providers_executing_termination = []

                for provider_name in cls._providers_pending_termination:
                    if provider_name not in cls._providers_executing_initialization:
                        logger.debug(
                            'Terminating {0}'.format(cls._providers_map_class[provider_name].api_class().__name__))

                        with cls._active_providers_lock.writer_lock:
                            cls._active_providers.remove(provider_name)

                        cls._providers_executing_termination[provider_name] = {
                            'api_class_event': Event(),
                            'epg_class_event': Event()
                        }

                        api_class_thread = Thread(
                            target=cls._providers_map_class[provider_name].api_class().terminate,
                            kwargs={
                                **cls._providers_pending_termination[provider_name],
                                'event': cls._providers_executing_termination[provider_name]['api_class_event']
                            }
                        )
                        api_class_thread.daemon = True
                        api_class_thread.start()

                        epg_class_thread = Thread(
                            target=cls._providers_map_class[provider_name].epg_class().terminate,
                            kwargs={
                                **cls._providers_pending_termination[provider_name],
                                'event': cls._providers_executing_termination[provider_name]['epg_class_event']
                            }
                        )
                        epg_class_thread.daemon = True
                        epg_class_thread.start()

                        providers_executing_termination.append(provider_name)

                for provider_name in providers_executing_termination:
                    del cls._providers_pending_termination[provider_name]
                # </editor-fold>

                # <editor-fold desc="Initialize providers">
                providers_executing_initialization = []

                for provider_name in cls._providers_pending_initialization:
                    if provider_name not in cls._providers_executing_initialization and \
                            provider_name not in cls._providers_executing_termination:
                        logger.debug(
                            'Reinitializing {0}'.format(cls._providers_map_class[provider_name].api_class().__name__))

                        with cls._active_providers_lock.writer_lock:
                            bisect.insort(cls._active_providers, provider_name)

                        cls._providers_executing_initialization[provider_name] = {
                            'api_class_event': Event(),
                            'epg_class_event': Event()
                        }

                        api_class_thread = Thread(
                            target=cls._providers_map_class[provider_name].api_class().initialize,
                            kwargs={
                                **cls._providers_pending_initialization[provider_name],
                                'event': cls._providers_executing_initialization[provider_name]['api_class_event']
                            }
                        )
                        api_class_thread.daemon = True
                        api_class_thread.start()

                        epg_class_thread = Thread(
                            target=cls._providers_map_class[provider_name].epg_class().initialize,
                            kwargs={
                                **cls._providers_pending_initialization[provider_name],
                                'event': cls._providers_executing_initialization[provider_name]['epg_class_event']
                            }
                        )
                        epg_class_thread.daemon = True
                        epg_class_thread.start()

                        providers_executing_initialization.append(provider_name)

                for provider_name in providers_executing_initialization:
                    del cls._providers_pending_initialization[provider_name]
                # </editor-fold>

                cls._wait_event.clear()

            if any((cls._providers_executing_initialization,
                    cls._providers_executing_termination,
                    cls._providers_pending_initialization,
                    cls._providers_pending_termination)):
                time.sleep(1)
            else:
                cls._wait_event.wait()

            if cls._stop_event.is_set():
                with cls._active_providers_lock.reader_lock:
                    for provider_name in cls._active_providers[:]:
                        logger.debug(
                            'Terminating {0}'.format(cls._providers_map_class[provider_name].api_class().__name__))

                        cls._providers_map_class[provider_name].api_class().terminate(Event())
                        cls._providers_map_class[provider_name].epg_class().terminate(Event())

                        cls._active_providers.remove(provider_name)

                break

    @classmethod
    def get_active_providers(cls):
        with cls._active_providers_lock.reader_lock:
            return tuple(cls._active_providers)

    @classmethod
    def get_active_providers_map_class(cls):
        active_providers_map_class = {}

        with cls._active_providers_lock.reader_lock:
            for provider_name in cls._active_providers:
                active_providers_map_class[provider_name] = cls._providers_map_class[provider_name]

        return active_providers_map_class

    @classmethod
    def get_active_provider_map_class(cls, provider_name):
        with cls._active_providers_lock.reader_lock:
            if provider_name in cls._active_providers:
                return cls._providers_map_class[provider_name]

        logger.error('Provider {0} is inactive'.format(provider_name))

        raise ProviderNotFoundError

    @classmethod
    def get_providers_map_class(cls):
        return copy.copy(cls._providers_map_class)

    @classmethod
    def get_provider_map_class(cls, provider_name):
        return cls._providers_map_class[provider_name]

    @classmethod
    def initialize(cls):
        cls._initialize_providers_map_class()

        for provider_name in cls._providers_map_class:
            cls._providers_map_class[provider_name].database_class().initialize()

        providers_controller_thread = Thread(target=cls._run)
        providers_controller_thread.daemon = True

        providers_controller_thread.start()

    @classmethod
    def initialize_provider(cls, provider_name, **kwargs):
        with cls._providers_initialization_termination_lock:
            if provider_name in cls._providers_pending_termination:
                # Don't terminate the provider if we'll be reinitializing it anyways
                del cls._providers_pending_termination[provider_name]

            cls._providers_pending_initialization[provider_name] = kwargs

            cls._wait_event.set()

    @classmethod
    def initialize_providers(cls, active_providers):
        for provider_name in active_providers:
            logger.debug('Initializing {0}'.format(cls._providers_map_class[provider_name].api_class().__name__))

            try:
                cls._providers_map_class[provider_name].api_class().initialize()
                cls._providers_map_class[provider_name].epg_class().initialize()

                cls._active_providers.append(provider_name)
            except Exception:
                logger.error('Failed to initialize {0}'.format(
                    cls._providers_map_class[provider_name].api_class().__name__))

                (status, value_, traceback_) = sys.exc_info()

                logger.error('\n'.join(traceback.format_exception(status, value_, traceback_)))

    @classmethod
    def set_active_providers(cls, active_providers):
        with cls._active_providers_lock.writer_lock:
            cls._active_providers = sorted(active_providers)

    @classmethod
    def terminate(cls):
        cls._stop_event.set()

    @classmethod
    def terminate_provider(cls, provider_name, **kwargs):
        with cls._providers_initialization_termination_lock:
            if provider_name in cls._providers_pending_initialization:
                # Don't initialize the provider if we'll be terminating it anyways
                del cls._providers_pending_initialization[provider_name]

            if provider_name not in cls._providers_executing_termination:
                # No point in terminating a provider that is being terminated
                cls._providers_pending_termination[provider_name] = kwargs

                cls._wait_event.set()
