
init -3 python in _shooter:

    class Enemy(Player):

        __author__ = "Vladya"

        _bullet_picture = im.FactorScale(
            "RenPyShooterPictures/bullet_hole.png",
            .2
        )
        AGRESSIVE = .1  # Показатель "агрессии". Как часто противник атакует.

        def __init__(
            self,
            sprite,
            damage_mask,
            flash_picture=None,
            gun_class=None,
            **properties
        ):

            """
            :doc: 'EnemySprite'
            :flash_picture:
                Спрайт выстрела противника.
            :gun_class:
                Класс оружия, или None.
            """

            flash_picture_properties = renpy.easy.split_properties(
                properties,
                "flash_picture_",
                ""
            )[0]
            flash_picture_properties["rotate"] = 0

            super(Enemy, self).__init__(
                gun_class=gun_class,
                mouse="current_on_enemy"
            )
            self._sprite = EnemySprite(sprite, damage_mask)
            self.bullet_picture = _displayable(self._bullet_picture)
            if flash_picture:
                self.flash_picture = TimeTransform(
                    _displayable(flash_picture),
                    align=(0, 0)
                )
                self.flash_picture._set_params(**flash_picture_properties)
            else:
                self.flash_picture = None
            self.sprite_width = self.sprite_height = None
            self._bullet_wounds = []

            self._start_acttack_time = None

            self._attack_zoom = 1.  # Зум при атаке.
            self._last_zoom_time = .0

            self._dead_animation = TimeTransform(xalign=.5, yalign=1.)
            self._rend_offset = None

            self._at_gunpoint = None

        @property
        def start_acttack_time(self):
            if not self._start_acttack_time:
                self._start_acttack_time = (
                    (random.uniform(.5, 1.) / self.AGRESSIVE)
                )
            return self._start_acttack_time

        def _is_melee_distance(self):
            return (self._attack_zoom >= self.MELEE_DISTANCE)

        def _at_gunpoint_action(self, event_object):
            pass  # Для переопределения при необходимости.

        def _not_at_gunpoint_action(self):
            pass

        def visit(self):
            result = [self._sprite]
            result.extend(map(lambda x: x.picture, self._bullet_wounds))
            return result

        def event(self, ev, x, y, st):

            if self._can_hide:
                return

            if not (self.sprite_width and self.sprite_height):
                return

            if self._rend_offset:
                xoff, yoff = self._rend_offset
                x -= xoff
                y -= yoff

            if self._attack_zoom <= .0:
                x = y = float("+inf")
            else:
                x, y = map(lambda a: absolute((a / self._attack_zoom)), (x, y))
            if not all(
                (
                    (.0 <= x < self.sprite_width),
                    (.0 <= y < self.sprite_height)
                )
            ):
                # Курсор в иной части экрана.
                if self._at_gunpoint:
                    self._at_gunpoint = False
                    self._not_at_gunpoint_action()
                return
            r, g, b, a = self._sprite._get_at(x, y)
            if not a:
                # Курсор в области спрайта, но в прозрачной области маски.
                if self._at_gunpoint:
                    self._at_gunpoint = False
                    self._not_at_gunpoint_action()
                return
            if not self._need_handle_shooter_event(ev):
                return

            if isinstance(ev._event_object, ShotEvent):

                armor_coefficient = (g * a)
                damage_coefficient = ((r * a) * (1. - armor_coefficient))
                gun_coefficient = ev._event_object.gun.DAMAGE_COEFFICIENT

                damage_value = damage_coefficient * gun_coefficient
                if damage_value > .0:
                    if isinstance(ev._event_object.gun, Melee):
                        if not self._is_melee_distance():
                            damage_value = .0
                    else:
                        bullet_picture = Transform(
                            self.bullet_picture,
                            rotate=random.randint(0, 359),
                            zoom=random.uniform(.9, 1.)
                        )
                        bullet = BulletInfo(bullet_picture, x, y)
                        self._bullet_wounds.append(bullet)
                self.health_point = (
                    max(min((self.health_point - damage_value), 1.), .0)
                )

            elif isinstance(ev._event_object, AtGunpointEvent):
                if not self._at_gunpoint:
                    self._at_gunpoint = True
                    self._at_gunpoint_action(event_object=ev._event_object)

            raise renpy.IgnoreEvent()

        def render(self, width, height, st, at):

            if self._can_hide:
                return renpy.Render(1, 1)

            rend = renpy.render(self._sprite, width, height, st, at)
            self.sprite_width, self.sprite_height = map(
                absolute,
                rend.get_size()
            )
            render_object = renpy.Render(rend.width, rend.height)
            render_object.blit(rend, (0, 0))
            if self._action and self._at_gunpoint:
                render_object.add_focus(
                    self,
                    None,
                    0, 0,
                    render_object.width, render_object.height,
                    0, 0,
                    render_object
                )
            for picture, x, y in self._bullet_wounds:
                picture_rend = renpy.render(picture, width, height, st, at)
                x -= (picture_rend.width * .5)
                y -= (picture_rend.height * .5)
                x, y = map(absolute, (x, y))
                rend_for_blit = renpy.Render(
                    (picture_rend.width + x),
                    (picture_rend.height + y)
                )
                # Для корректного зума blit должен быть только (0, 0).
                rend_for_blit.blit(picture_rend, (x, y))
                render_object.blit(rend_for_blit, (0, 0))

            time_after_last_shot = (st - self.gun._last_shot_time)

            if (not isinstance(self.gun, Melee)) and self.flash_picture:
                if time_after_last_shot <= self.gun.TIME_TO_ONE_SHOT:
                    #  Отрисовка вспышки выстрела.
                    flash_render = renpy.render(
                        self.flash_picture,
                        width,
                        height,
                        st,
                        at
                    )
                    _xpos, _ypos = self.flash_picture.state.pos
                    _xanchor, _yanchor = self.flash_picture.state.anchor
                    if isinstance(_xanchor, float):
                        _xanchor *= flash_render.width
                    if isinstance(_yanchor, float):
                        _yanchor *= flash_render.height
                    if isinstance(_xpos, float):
                        _xpos *= render_object.width
                    if isinstance(_ypos, float):
                        _ypos *= render_object.height
                    x, y = map(
                        absolute,
                        ((_xpos - _xanchor), (_ypos - _yanchor))
                    )
                    rend_for_blit = renpy.Render(
                        (flash_render.width + x),
                        (flash_render.height + y)
                    )
                    rend_for_blit.blit(flash_render, (x, y))
                    render_object.blit(rend_for_blit, (0, 0))

            if self.is_alive() and (self.AGRESSIVE > .0):
                can_attack = True
                if isinstance(self.gun, Melee):
                    if not self._is_melee_distance():
                        # Чтобы атаковать в мили, - надо сначала подойти.
                        can_attack = False
                        step_speed = self.AGRESSIVE
                        addition = (st - self._last_zoom_time) * step_speed
                        new_zoom = (self._attack_zoom + addition)
                        if self._action:
                            if new_zoom >= self.MELEE_DISTANCE:
                                self._attack_zoom = self.MELEE_DISTANCE
                                can_attack = True
                            else:
                                self._attack_zoom = new_zoom
                        self._last_zoom_time = st
                if can_attack and (st >= self.start_acttack_time):
                    _enemy_cooldown = (.3 / self.AGRESSIVE)
                    if time_after_last_shot > _enemy_cooldown:
                        if self._action:
                            self.gun.pull_the_trigger()
                            if self.flash_picture:
                                self.flash_picture._set_params(
                                    rotate=random.randint(0, 359)
                                )
                    else:
                        self.gun.release_the_trigger()

            # Оружие у противника не демонстрируется,
            # но рендер нужен для обработки ивентов.
            _gun_render = renpy.render(self.gun, width, height, st, at)

            new_w = int((render_object.width * self._attack_zoom))
            new_h = render_object.height
            render_object = render_object.subsurface(
                (0, 0, new_w, new_h),
                True
            )
            render_object.zoom(self._attack_zoom, self._attack_zoom)

            if (not self._can_hide) and (not self.is_alive()):
                # Враг убит. Анимация смерти.
                if not self._dead_animation._is_changing():
                    self._dead_animation.change_values_over_time(
                        random.uniform(.1, .5),
                        xanchor=random.uniform((-.1), 1.1),
                        yanchor=(-1.5),
                        callback=renpy.partial(
                            setattr,
                            self,
                            "_can_hide",
                            True
                        )
                    )

                w, h = map(absolute, render_object.get_size())
                _new_render = renpy.Render(w, h)
                xpos, ypos = self._dead_animation.state.pos
                xanchor, yanchor = self._dead_animation.state.anchor
                x = (w * xpos) - (w * xanchor)
                y = (h * ypos) - (h * yanchor)
                self._rend_offset = (x, y)
                _new_render.blit(render_object, (x, y))
                render_object = _new_render
            renpy.render(self._dead_animation, width, height, st, at)
            renpy.redraw(self, .0)
            return render_object

    class EnemySprite(im.ImageBase):

        """
        Предварительные преобразования спрайта врага.

        :damage_mask:

            Изображение используемое для рассчёта нанесённого урона.
            Предполагается, что размер и формат соответствует основному.

            Пиксель маски будет интерпретирован следующим образом:
                Значение красного (0x00 - 0xff):
                    Уровень повреждения, 0x00 - мисс.
                Значение зелёного (0x00 - 0xff):
                    Показатель брони. 0xff - неуязвимость, 0x00 - без защиты.
                Значение синего (0x00 - 0xff):
                    Игнорируется (может позже придумаю что нибудь забавное).
                Значение альфа канала:
                    Ожидается соответствие оригиналу.
        """

        __author__ = "Vladya"

        def __init__(self, image, damage_mask):

            try:
                image = im.image(image)
                damage_mask = im.image(damage_mask)
            except Exception as ex:
                raise ValueError(ex.message)

            _fn = getattr(image, "filename", None)
            if isinstance(_fn, basestring):
                ext = path.splitext(path.normpath(_fn))[-1]
                if ext.lower() in (".jpg", ".jpeg"):
                    # Удаляем белый фон у JPG изображения.
                    image = self._remove_white_color(image)
                    damage_mask = self._remove_white_color(damage_mask)

            super(EnemySprite, self).__init__(image, damage_mask)
            self.__image = image
            self.__damage_mask = damage_mask

            self.__damage_mask_surface = None

        @staticmethod
        def _remove_white_color(image):
            try:
                image = im.image(image)
            except Exception as ex:
                raise ValueError(ex.message)
            return im.MatrixColor(
                image,
                (
                     1.0,  0.0,  0.0, 0.0, 0.0,
                     0.0,  1.0,  0.0, 0.0, 0.0,
                     0.0,  0.0,  1.0, 0.0, 0.0,
                    -1.0, -1.0, -1.0, 3.0, 0.0
                )
            )

        def _get_at(self, x, y):
            x, y = map(int, (x, y))
            r, g, b, a = map(
                lambda x: (float(x) / 0xff),
                self.damage_mask_surface.get_at((x, y))
            )
            return (r, g, b, a)

        @property
        def damage_mask_surface(self):
            if self.__damage_mask_surface:
                return self.__damage_mask_surface
            self.__damage_mask_surface = im.cache.get(self.__damage_mask)
            return self.__damage_mask_surface

        def predict_files(self):
            result = []
            result.extend(self.__image.predict_files())
            result.extend(self.__damage_mask.predict_files())
            return result

        def load(self):
            return im.cache.get(self.__image)
