
init -10 python in _shooter:

    import random
    import math
    import collections
    import pygame_sdl2 as pygame
    from os import path
    from renpy.display.core import absolute
    from store import (
        im,
        Transform,
        Null,
        NoRollback
    )

    _audio_formats = frozenset({".wav", ".mp2", ".mp3", ".ogg", ".opus"})
    BulletInfo = collections.namedtuple("BulletInfo", "picture x y")

    def _displayable(data):
        """
        Небольшая обёртка над 'renpy.easy.displayable',
        гарантирующая возврат обекта Displayable.
        """
        try:
            disp = renpy.easy.displayable(data)
        except Exception:
            disp = None
        if not isinstance(disp, renpy.display.core.Displayable):
            raise ValueError(
                __(
                    "'{0!r}' не может быть интерпретировано как 'displayable'."
                ).format(data)
            )
        return disp

    class EnemyInteractionEvent(object):

        """
        Ивенты, взаимодействующие между игроком и "врагом".
        """

        def __init__(self, assaulter):

            """
            :assaulter:
                Тот кто начал взаимодействие.
                Объект класса 'PlayerPOV' или 'Enemy'
            """
            if not isinstance(assaulter, Player):
                raise TypeError(__("Некорректное значение 'assaulter'."))
            self.assaulter = assaulter

    class ImageBaseNull(im.ImageBase):

        __author__ = "Vladya"

        def __init__(self, width, height):
            width, height = map(int, (width, height))
            super(ImageBaseNull, self).__init__(width, height)
            self.size = (width, height)

        def load(self):
            return renpy.display.pgrender.surface(self.self.size, True)


init 100 python in _renpyshootercursorsetting:

    from store import (
        config,
        im,
        _shooter
    )

    PLACEHOLDER_MOUSE = (
        (im.image("RenPyShooterPictures/cursor_placeholder.png"), 0, 0),
    )
    DEFAULT_CROSSHAIR = (
        (im.FactorScale("RenPyShooterPictures/crosshair.png", .3), 30, 30),
    )
    DEFAULT_ON_ENEMY = tuple(
        map(
            lambda x: (
                im.MatrixColor(
                    x[0],
                    (
                        0, 0, 0, 0, 1,
                        0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0,
                        0, 0, 0, 1, 0
                    )
                ),
                x[1],
                x[2]
            ),
            DEFAULT_CROSSHAIR
        )
    )
    NULL_CURSOR = ((_shooter.ImageBaseNull(1, 1), 0, 0),)

    if not config.mouse:
        #
        # Если на поздних этапах инициализации
        # курсор не определён - ставим форсированно,
        # т.к. для корректного отображения прицела
        # нужны взаимодействия с переменной 'config.mouse'
        #
        config.mouse = {"default": PLACEHOLDER_MOUSE}

    config.mouse.update(
        {
            "null_cursor": NULL_CURSOR,
            "default_crosshair": DEFAULT_CROSSHAIR,
            "default_on_enemy": DEFAULT_ON_ENEMY
        }
    )
    #  Обновляемые значения под конкретное оружие.
    config.mouse["current_crosshair"] = config.mouse["default_crosshair"]
    config.mouse["current_on_enemy"] = config.mouse["default_on_enemy"]
