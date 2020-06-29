
init -9 python in _shooter:

    class AudioWrapper(object):

        __author__ = "Vladya"

        BASETAG = "RenPyShooterSFXChannel"
        _audio_formats = frozenset({".wav", ".mp2", ".mp3", ".ogg", ".opus"})

        def __init__(self, num_of_channel=10):
            self.__channels = tuple(
                self._register_sfx_channels(num_of_channel)
            )
            self.__last_channel = self.__channels[-1]

        def play_sfx(self, data):
            """
            Для эффекта перекрытия, каждый новый звук будет проигрываться
            на очередном канале, что даст возможность затихнуть звуку
            предыдущего выстрела/перезарядки, когда звучит последующий.
            """
            _last_index = self.__channels.index(self.__last_channel)
            _new_index = ((_last_index + 1) % len(self.__channels))
            _channel = self.__channels[_new_index]
            renpy.audio.music.play(data, channel=_channel)
            self.__last_channel = _channel

        def _playable(self, data):
            try:
                self._raise_with_sound(data)
            except Exception:
                return False
            else:
                return True

        def _raise_with_sound(self, data):
            """
            Проверяет аудио и бросает трейс, если оно некорректно.
            """
            if not isinstance(data, basestring):
                raise TypeError(__("Некорректный тип аудио."))
            _ext = path.splitext(path.normpath(data))[-1]
            if _ext.lower() not in _audio_formats:
                raise ValueError(__("Некорректный формат аудио."))
            if not renpy.audio.music.playable(data, self.__channels[0]):
                raise ValueError(__("Невозможно загрузить аудиофайл."))

        @classmethod
        def _register_sfx_channels(cls, num_of_channel):
            """
            Возвращает генератор имён зарегистрированных каналов.
            :num_of_channel:
                Количество каналов.
            """
            for _i in xrange(num_of_channel):
                counter = 0
                while True:
                    _chan_name = '_'.join((cls.BASETAG, unicode(counter)))
                    if _chan_name not in renpy.audio.audio.channels:
                        renpy.music.register_channel(
                            name=_chan_name,
                            mixer="sfx",
                            loop=False
                        )
                        yield _chan_name
                        break
                    counter += 1

    _audio = AudioWrapper(10)
