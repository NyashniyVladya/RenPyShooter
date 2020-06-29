
init -4 python in _shooter:

    class Player(renpy.Displayable):

        """
        Абстрактный класс для игрока - юзера, или "врага".
        """

        __author__ = "Vladya"

        MELEE_DISTANCE = 2.5

        def __init__(self, gun_class=None, **kwargs):

            super(Player, self).__init__(**kwargs)

            if gun_class is not None:
                if not hasattr(gun_class, "__mro__"):
                    raise ValueError(__("Передан не класс."))
                if Gun not in gun_class.__mro__:
                    raise TypeError(__("Неверный тип класса оружия."))
                self.gun = gun_class(shooter=self)
            else:
                self.gun = Melee(shooter=self)
            self.health_point = 1.
            self._can_hide = False  # True, если враг/юзер убит. Скрываем.
            self._action = False  # Идёт ли бой. Для активации паузы.

        def is_alive(self):
            return (self.health_point > .0)

        def _need_handle_shooter_event(self, ev):
            if ev.type != renpy.display.core.EVENTNAME:
                return False
            if "ShooterEvent" not in ev.eventnames:
                return False
            if not isinstance(ev._event_object, EnemyInteractionEvent):
                return False
            if isinstance(ev._event_object.assaulter, self.__class__):
                # Ивент послан самим объектом. Не обрабатываем.
                return False
            return True

        def render(self, width, height, st, at):
            raise NotImplementedError(
                __("Метод рендера должен быть переопределён.")
            )

    class PlayerPOV(Player):

        """
        Класс юзера.
        """

        _damage_indicator = "RenPyShooterPictures/dmg_indicator.png"
        _damage_picture = "RenPyShooterPictures/damaged.png"
        _critical_damage_picture = "RenPyShooterPictures/critical_damaged.png"
        DEMONSTRATE_DAMAGE_TIME = .5  # Время показа картинки повреждений.

        ARMOR_COEFFICIENT = .8  # Показатель брони. 1.0 - неуязвимость.

        SHOT_MOUSEBUTTONS = frozenset({1,})
        SHOT_BUTTONS = frozenset({pygame.K_z, pygame.K_x})

        def __init__(self, gun_class=None):
            super(PlayerPOV, self).__init__(gun_class=gun_class)
            self.__damage_indicator = TimeTransform(
                _displayable(self._damage_indicator),
                alpha=.0
            )
            self.__damage_picture = TimeTransform(self._damage_picture)
            self.__critical_damage_picture = TimeTransform(
                self._critical_damage_picture
            )
            self.__triggers = {}
            self.__triggers.update(
                map(
                    lambda x: ("mousebutton_{0}".format(x), False),
                    self.SHOT_MOUSEBUTTONS
                )
            )
            self.__triggers.update(
                map(
                    lambda x: ("key_{0}".format(x), False),
                    self.SHOT_BUTTONS
                )
            )
            self.__trigger_value = False
            self.__current_mouse = (0, 0)

        def event(self, ev, x, y, st):
            # Обрабатываем действия юзера, и пересылаем их как ивенты шутера.
            if not self.is_alive():
                return

            self.__current_mouse = (x, y)
            if ev.type in (
                pygame.MOUSEMOTION,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEBUTTONDOWN
            ):
                if not isinstance(self.gun, Melee):
                    # Наведение прицела.
                    event = AtGunpointEvent(assaulter=self, gun=self.gun)
                    renpy.queue_event("ShooterEvent", _event_object=event)

            _dictkey = None
            if ev.type in (pygame.KEYDOWN, pygame.KEYUP):
                _dictkey = "key_{0}".format(ev.key)
            elif ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                _dictkey = "mousebutton_{0}".format(ev.button)

            if _dictkey and (_dictkey in self.__triggers):
                self.__triggers[_dictkey] = (
                    (ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN))
                )
                _trigger_value = any(self.__triggers.itervalues())
                if self.__trigger_value != _trigger_value:
                    self.__trigger_value = _trigger_value
                    if _trigger_value:
                        if self._action:
                            self.gun.pull_the_trigger()
                    else:
                        self.gun.release_the_trigger()
                raise renpy.IgnoreEvent()

            if not self._need_handle_shooter_event(ev):
                return

            if isinstance(ev._event_object, ShotEvent):
                # По юзеру стреляют.
                can_attack = True
                if isinstance(ev._event_object.gun, Melee):
                    if not ev._event_object.assaulter._is_melee_distance():
                        # Если враг машет кулаками "в никуда".
                        can_attack = False
                if can_attack:
                    self.__damage_indicator._stop_changes()
                    self.__damage_indicator._set_params(alpha=1.)
                    self.__damage_indicator.change_values_over_time(
                        self.DEMONSTRATE_DAMAGE_TIME,
                        alpha=.0,
                        warper=lambda x: (math.expm1(x) / math.expm1(1.))
                    )
                    damage_value = ev._event_object.gun.DAMAGE_COEFFICIENT
                    damage_value *= (1. - self.ARMOR_COEFFICIENT)
                    self.health_point = (
                        max(min((self.health_point - damage_value), 1.), .0)
                    )

            raise renpy.IgnoreEvent()

        def visit(self):
            return [
                self.__damage_indicator,
                self.__damage_picture,
                self.__critical_damage_picture,
                self.gun
            ]

        def render(self, width, height, st, at):

            render_object = renpy.Render(width, height)
            if not self.is_alive():
                render_object.fill((0xff, 0x00, 0x00, 0xff))
                self._can_hide = True
                return render_object

            # Отрисовка оружия.
            gun_render = renpy.render(self.gun, width, height, st, at)
            _w, _h = map(absolute, gun_render.get_size())
            _screen_pos_x = _screen_pos_y = 1.
            xanchor, yanchor = map(
                lambda a: (1. - ((float(a[0]) / a[1]) * .25)),
                zip(self.__current_mouse, (width, height))
            )
            xpos = (width * _screen_pos_x) - (_w * xanchor)
            ypos = (height * _screen_pos_y) - (_h * yanchor)
            if self.gun._current_state != self.gun.OK_STATE:
                # Движение при анимации перезарядки.
                xoffset, yoffset = self.gun._reload_anim.state.offset
                xpos += xoffset
                ypos += yoffset
            pos = tuple(map(absolute, (xpos, ypos)))
            render_object.blit(gun_render, pos)

            if self.health_point < 1.:
                # Отрисовка картинки повреждения.
                _damage = (1. - self.health_point)
                self.__damage_picture._set_params(
                    alpha=(_damage ** 2.)
                )
                self.__critical_damage_picture._set_params(
                    alpha=(_damage ** 3.)
                )
                damage_picture_render = renpy.render(
                    self.__damage_picture,
                    width,
                    height,
                    st,
                    at
                )
                critical_damage_picture_render = renpy.render(
                    self.__critical_damage_picture,
                    width,
                    height,
                    st,
                    at
                )
                render_object.blit(damage_picture_render, (0, 0))
                render_object.blit(critical_damage_picture_render, (0, 0))
                render_object.fill(
                    (0xff, 0x00, 0x00, int((0xff * (_damage ** 4.))))
                )

            damage_indicator_render = renpy.render(
                self.__damage_indicator,
                width,
                height,
                st,
                at
            )
            render_object.blit(damage_indicator_render, (0, 0))

            renpy.redraw(self, .0)
            return render_object
