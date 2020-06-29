
init -4 python in _shooter:

    class BattleField(renpy.Displayable, NoRollback):

        __author__ = "Vladya"
        GLOBAL_NAME = "_RenPyShooterDisp"
        _raw_args = None  # Нераспакованные аргументы поля боя.

        def __init__(self, background, player_gun_class=None, *enemies):
            """
            :player_gun_class:
                Класс оружия main чара.
            :other doc: '_WideScreenBattleField'
            """
            self._init_args = ((background, player_gun_class) + enemies)
            super(BattleField, self).__init__(mouse="current_crosshair")

            self._player_pov = PlayerPOV(player_gun_class)
            self._battlefield = Panorama(
                _WideScreenBattleField(background, *enemies)
            )
            self._crosshair_is_set = False
            self._pause()

        def __getstate__(self):
            return (self._raw_args or {})

        def __setstate__(self, raw_args):
            """
            Поддержка сохранений в момент когда объект на экране и бой не идёт.
            При загрузке отобразится изначальное состояние "поля боя".
            """
            if not raw_args:
                raise Exception(__("Объект был инициализирован некорректно."))
            _parser = store._shooter_statements.ShooterStatementParser
            _args = _parser._evaluate_args(raw_args)
            new_bf = _parser.get_battlefield_object_from_arg_dict(_args)
            self.__init__(*new_bf._init_args)
            self._raw_args = raw_args.copy()

        def _start(self):
            self._action = True
            self._update_players_status()

        def _pause(self):
            self._action = False
            self._update_players_status()

        def _update_players_status(self):
            self._player_pov._action = self._action
            for en in self._battlefield._child._enemies:
                en["enemy"]._action = self._action

        def visit(self):
            return [self._player_pov, self._battlefield]

        def event(self, ev, x, y, st):
            self._player_pov.event(ev, x, y, st)
            self._battlefield.event(ev, x, y, st)

        def render(self, *rend_args):

            if not self._crosshair_is_set:
                _crosshair = self._player_pov.gun._crosshair
                if not _crosshair:
                    _crosshair = renpy.config.mouse["default_crosshair"]
                _on_enemy = self._player_pov.gun._crosshair_on_enemy
                if not _on_enemy:
                    _on_enemy = renpy.config.mouse["default_on_enemy"]
                renpy.config.mouse.update(
                    {
                        "current_crosshair": _crosshair,
                        "current_on_enemy": _on_enemy
                    }
                )
                self._crosshair_is_set = True

            if self._action:
                if self._player_pov._can_hide:
                    # Проигрыш. Персонаж убит.
                    self._pause()
                    renpy.end_interaction(False)

                for en in self._battlefield._child._enemies:
                    if not en["enemy"]._can_hide:
                        # Имеется минимум один живой враг.
                        break
                else:
                    # Врагов не осталось.
                    self._pause()
                    renpy.end_interaction(True)

            battlefield_rend = renpy.render(self._battlefield, *rend_args)
            render_object = renpy.Render(
                battlefield_rend.width,
                battlefield_rend.height
            )
            if self._action:
                render_object.add_focus(
                    self,
                    w=battlefield_rend.width,
                    h=battlefield_rend.height
                )
            render_object.blit(battlefield_rend, (0, 0))

            player_rend = renpy.render(self._player_pov, *rend_args)
            render_object.blit(player_rend, (0, 0))
            renpy.redraw(self, .0)
            return render_object

    class _WideScreenBattleField(renpy.Displayable):

        """
        Поле боя.
        """

        __author__ = "Vladya"

        def __init__(self, background, *enemies):

            """
            :background:
                Фон.
            :enemies:
                Кортеж объектов 'Enemy'.
            """

            super(_WideScreenBattleField, self).__init__()
            self._background = _displayable(background)
            self._enemies = tuple(
                map(
                    lambda enemy: {
                        "enemy": enemy,
                        "xalign": random.random(),
                        "yalign": 1.,
                        "pos": None
                    },
                    enemies
                )
            )

        def visit(self):
            result = [self._background]
            result.extend(map(lambda x: x["enemy"], self._enemies))
            return result

        def event(self, ev, x, y, st):
            for enemy_info in reversed(self._enemies):
                if enemy_info["enemy"]._can_hide:
                    continue
                if not enemy_info["pos"]:
                    continue
                xpos, ypos = enemy_info["pos"]
                enemy_x = (x - xpos)
                enemy_y = (y - ypos)
                enemy_info["enemy"].event(ev, enemy_x, enemy_y, st)

        def render(self, *rend_args):

            # Сначала отрисовываем фонец.
            back_rend = renpy.render(self._background, *rend_args)
            w, h = map(absolute, back_rend.get_size())
            render_object = renpy.Render(w, h)
            render_object.blit(back_rend, (0, 0))

            # Потом врагов.
            # Если кто-то успел подбежать ближе - рисуем его перед дальним.
            # А так же удаляем выбывших, чтобы не занимали память.
            self._enemies = tuple(
                sorted(
                    filter(
                        lambda en: (not en["enemy"]._can_hide),
                        self._enemies
                    ),
                    key=lambda en: en["enemy"]._attack_zoom
                )
            )
            for enemy_info in self._enemies:
                if enemy_info["enemy"]._can_hide:
                    continue
                enemy_rend = renpy.render(enemy_info["enemy"], *rend_args)
                _w, _h = map(absolute, enemy_rend.get_size())
                xpos = (w * enemy_info["xalign"]) - (_w * enemy_info["xalign"])
                ypos = (h * enemy_info["yalign"]) - (_h * enemy_info["yalign"])
                enemy_info["pos"] = tuple(map(int, (xpos, ypos)))
                render_object.blit(enemy_rend, enemy_info["pos"])

            renpy.redraw(self, .0)
            return render_object

    class Panorama(renpy.Displayable):

        """
        Даёт возможность перемещаться по широкому изображению,
        изменяя его положение относительно движения мыши.
        """

        __author__ = "Vladya"

        def __init__(self, child):

            super(Panorama, self).__init__()
            self._child = _displayable(child)
            self.width = self.height = None
            self.child_w = self.child_h = None
            self.__align = (.5, .5)

        def visit(self):
            return [self._child]

        def event(self, ev, x, y, st):

            if not all(
                map(
                    lambda x: (x is not None),
                    (self.width, self.height, self.child_w, self.child_h)
                )
            ):
                renpy.redraw(self, .0)
                return

            x, y = map(absolute, (x, y))
            if not ((.0 <= x <= self.width) and (.0 <= y <= self.height)):
                return

            self.__align = ((x / self.width), (y / self.height))

            # Пересчитываем координаты относительно размеров 'child'.
            x *= (self.child_w / self.width)
            y *= (self.child_h / self.height)

            renpy.redraw(self, .0)
            return self._child.event(ev, x, y, st)

        def render(self, width, height, st, at):

            width, height = self.width, self.height = map(
                absolute,
                (width, height)
            )
            xalign, yalign = self.__align  # float

            render_object = renpy.Render(width, height)

            background_rend = renpy.render(self._child, width, height, st, at)
            w, h = self.child_w, self.child_h = map(
                absolute,
                background_rend.get_size()
            )

            xpos = ((w * xalign) - (width * xalign))
            ypos = ((h * yalign) - (height * yalign))
            background_rend = background_rend.subsurface(
                tuple(map(int, (xpos, ypos, width, height))),
                True
            )

            render_object.blit(background_rend, (0, 0))
            return render_object
