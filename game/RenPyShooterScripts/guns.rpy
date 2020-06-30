
init -4 python in _shooter:

    # Ивенты
    class GunEvent(EnemyInteractionEvent):

        """
        Ивенты, генерируемые классами оружия.
        """

        def __init__(self, assaulter, gun):
            super(GunEvent, self).__init__(assaulter)
            if not isinstance(gun, Gun):
                raise TypeError(__("Неверный тип оружия."))
            self.gun = gun

    class ShotEvent(GunEvent):
        """
        Выстрел.
        """

    class AtGunpointEvent(GunEvent):
        """
        Наведение прицела.
        """

    # #########################################

    class Gun(renpy.Displayable):

        """
        Абстрактный класс оружки, не предполагающий экземпляров.
        """

        __author__ = "Vladya"

        # "Убойная сила" оружия.
        DAMAGE_COEFFICIENT = None

        # Автоматическое ли оружие (если число - частичный автомат)
        AUTOMATIC = False

        # Скоростельность в "выстрелах-в-минуту".
        RATE_OF_FIRE = None

        # Время демонстрации "огня" на экране (сек.)
        TIME_TO_ONE_SHOT = None

        # Время на восстановление зума, после отдачи (сек.)
        RECOIL_RECOVERY_TIME = .5

        _DEFAULT_ZOOM = 1.

        # Предполагается одинаковый размер основной картинки и картинки огня.
        # Картинка огня будет подложена без сдвигов и масштабирований.
        _picture = None
        _fire_picture = None
        _fire_sound = None
        _no_bullet_sound = None

        _reload_gun_picture = None
        _reload_hand_with_patrons = None
        _bullet_picture = None
        _reload_sound = None

        _crosshair = None
        _crosshair_on_enemy = None

        RELOAD_TIME = 2.

        OK_STATE          = 1
        NEED_RELOAD_STATE = 2
        RELOAD_STATE1     = 3
        RELOAD_STATE2     = 4

        CAPACITY = None  # Ёмкость "магазина". None - бесконечный "магазин".

        def __init__(self, shooter, start_cap=None):

            """
            :shooter:
                Объект стрелка.
            """

            super(Gun, self).__init__()

            if not isinstance(shooter, Player):
                raise TypeError(__("Некорректное значение 'shooter'."))

            self.shooter = shooter

            self.picture = _displayable(self._picture)
            self.fire_picture = _displayable(self._fire_picture)
            if self._bullet_picture:
                self.bullet_picture = _displayable(self._bullet_picture)
            else:
                self.bullet_picture = Null()

            self._bullets = []  # Патроны в "магазине".
            self._patrons = []  # Стреляные "гильзы".
            if self.CAPACITY is not None:
                if (start_cap is None) or (start_cap > self.CAPACITY):
                    start_cap = self.CAPACITY
                for i in xrange(start_cap):
                    self._bullets.append(TimeTransform(self.bullet_picture))

            self.reload_gun_picture = None
            self.reload_hand_with_patrons = None
            if self._reload_gun_picture and self._reload_hand_with_patrons:
                self.reload_gun_picture = _displayable(
                    self._reload_gun_picture
                )
                self.reload_hand_with_patrons = _displayable(
                    self._reload_hand_with_patrons
                )

            self._rotate_fire_picture = False
            if isinstance(self.fire_picture, TimeTransform):
                if isinstance(self.fire_picture.state.rotate, int):
                    self._rotate_fire_picture = True

            _audio._raise_with_sound(self._fire_sound)
            self.fire_sound = self._fire_sound

            self.reload_sound = None
            if self._reload_sound:
                _audio._raise_with_sound(self._reload_sound)
                self.reload_sound = self._reload_sound

            self.no_bullet_sound = None
            if self._no_bullet_sound:
                _audio._raise_with_sound(self._no_bullet_sound)
                self.no_bullet_sound = self._no_bullet_sound

            self._trigger_is_pulled = False  # Спусковой крючок нажат.
            self._last_shot_time = float("-inf")  # Время последнего выстрела.
            self._automatic_counter = 0

            # Зум рендера. Для имитации отдачи.
            self._recoil_zoom = self._DEFAULT_ZOOM

            self._current_state = self.OK_STATE
            self._reload_anim = TimeTransform()

        @property
        def _current_capacity(self):
            """
            Количество патронов.
            """
            if self.CAPACITY is None:
                return float("+inf")
            return len(self._bullets)

        def pull_the_trigger(self):
            if self._current_state == self.OK_STATE:
                self._automatic_counter = 0
                self._trigger_is_pulled = True

        def release_the_trigger(self):
            self._trigger_is_pulled = False
            self._automatic_counter = 0

        def take_a_shot(self, st):
            """
            Делает 1 выстрел.
            :st:
                Время из метода рендера.
            """

            if self._current_state != self.OK_STATE:
                return

            if not self._current_capacity:
                if self._current_state == self.OK_STATE:
                    self._current_state = self.NEED_RELOAD_STATE
                    self._play_no_bullet_sound()
                return

            if isinstance(self.AUTOMATIC, bool):
                if not self.AUTOMATIC:
                    # Если оружка не автоматическая, - отжимаем сразу.
                    self._trigger_is_pulled = False
            elif isinstance(self.AUTOMATIC, int):
                # Частичная автоматика. Например на 3 выстрела без отжатия.
                self._automatic_counter += 1
                if self._automatic_counter >= self.AUTOMATIC:
                    self._automatic_counter = 0
                    self._trigger_is_pulled = False
            else:
                raise TypeError(__("Некорректный тип 'AUTOMATIC'."))

            if self._rotate_fire_picture:
                # Если картинка огня поддерживает перерисовку - делаем это.
                self.fire_picture._set_params(rotate=random.randint(0, 359))
            shooter_event = ShotEvent(assaulter=self.shooter, gun=self)
            renpy.queue_event(
                "ShooterEvent",
                _event_object=shooter_event
            )
            if isinstance(self, Melee):
                self._recoil_zoom = random.uniform(1., 1.05)
            else:
                self._recoil_zoom += random.uniform(.01, .02)
            self._last_shot_time = st
            if self._bullets:
                self._patrons.append(self._bullets.pop())
            if not self._current_capacity:
                if self._current_state == self.OK_STATE:
                    self._current_state = self.NEED_RELOAD_STATE
            self._play_fire_sound()

        def _play_fire_sound(self):
            _audio.play_sfx(self.fire_sound)

        def _play_reload_sound(self):
            if self.reload_sound:
                _audio.play_sfx(self.reload_sound)

        def _play_no_bullet_sound(self):
            if self.no_bullet_sound:
                _audio.play_sfx(self.no_bullet_sound)

        def visit(self):
            result = [
                self.picture,
                self.fire_picture,
                self.bullet_picture
            ]
            if self.reload_gun_picture:
                result.append(self.reload_gun_picture)
            if self.reload_hand_with_patrons:
                result.append(self.reload_hand_with_patrons)
            result.extend(self._bullets)
            result.extend(self._patrons)
            return result

        def render(self, width, height, st, at):

            if self._current_state == self.OK_STATE:
                render_object = self._ok_render(width, height, st, at)
            elif self._current_state in (
                self.NEED_RELOAD_STATE,
                self.RELOAD_STATE1,
                self.RELOAD_STATE2
            ):
                render_object = self._reload_render(width, height, st, at)
            else:
                raise NotImplementedError(
                    __("Рендер состояния {0} не определён.").format(
                        self._current_state
                    )
                )
            renpy.render(self._reload_anim, width, height, st, at)
            renpy.redraw(self, .0)
            return render_object

        def _reload_render(self, width, height, st, at):

            if self._current_state == self.NEED_RELOAD_STATE:
                # Этап первый. Убираем ствол из зоны видимости.
                ok_rend = self._ok_render(width, height, st, at)
                if not self._reload_anim._is_changing():
                    self._reload_anim = TimeTransform(offset=(0, 0))
                    self._reload_anim._st = st
                    self._reload_anim.change_values_over_time(
                        (self.RELOAD_TIME / 2.),
                        offset=tuple(map(int, ok_rend.get_size())),
                        callback=renpy.partial(
                            setattr,
                            self,
                            "_current_state",
                            self.RELOAD_STATE1
                        )
                    )
                return ok_rend

            elif self._current_state == self.RELOAD_STATE1:
                # Этап второй. Заряжаем и возвращаем.
                ok_rend = self._ok_render(width, height, st, at)
                if not self._reload_anim._is_changing():
                    self._bullets = []
                    self._patrons = []
                    if self.CAPACITY is not None:
                        self._play_reload_sound()
                        for i in xrange(self.CAPACITY):
                            self._bullets.append(
                                TimeTransform(self.bullet_picture)
                            )
                    self._reload_anim = TimeTransform(
                        offset=tuple(map(int, ok_rend.get_size()))
                    )
                    self._reload_anim._st = st
                    self._reload_anim.change_values_over_time(
                        (self.RELOAD_TIME / 2.),
                        offset=(0, 0),
                        callback=renpy.partial(
                            setattr,
                            self,
                            "_current_state",
                            self.RELOAD_STATE2
                        )
                    )
                return ok_rend
            elif self._current_state == self.RELOAD_STATE2:
                # Заключительный. Сбрасываем трансу.
                ok_rend = self._ok_render(width, height, st, at)
                self._reload_anim = TimeTransform()
                self._reload_anim._st = st
                self._current_state = self.OK_STATE
                return ok_rend
            else:
                raise NotImplementedError(
                    __("Рендер состояния {0} не определён.").format(
                        self._current_state
                    )
                )

        def _ok_render(self, width, height, st, at):

            """
            Рендер обычного режима огня.
            """

            time_after_last_shot = (st - self._last_shot_time)

            pic_rend = renpy.render(self.picture, width, height, st, at)
            render_object = renpy.Render(pic_rend.width, pic_rend.height)

            if time_after_last_shot <= self.TIME_TO_ONE_SHOT:
                # Время отрисовки огня ещё не прошло. Рисуем.
                fire_rend = (
                    renpy.render(self.fire_picture, width, height, st, at)
                )
                if isinstance(self.fire_picture, TimeTransform):
                    w, h = map(absolute, fire_rend.get_size())
                    xanchor, yanchor = self.fire_picture.state.anchor
                    xpos, ypos = self.fire_picture.state.pos
                    if None not in (xanchor, yanchor, xpos, ypos):
                        if isinstance(xanchor, float):
                            xanchor *= w
                        if isinstance(yanchor, float):
                            yanchor *= h
                        if isinstance(xpos, float):
                            xpos *= pic_rend.width
                        if isinstance(ypos, float):
                            ypos *= pic_rend.height
                        x, y = map(
                            absolute,
                            ((xpos - xanchor), (ypos - yanchor))
                        )
                        new_render = renpy.Render((x + w), (y + h))
                        new_render.blit(fire_rend, (x, y))
                        fire_rend = new_render

                render_object.blit(fire_rend, (0, 0))
            render_object.blit(pic_rend, (0, 0))

            # zoom отдачи/удара
            if self.RECOIL_RECOVERY_TIME <= .0:
                percent_of_path = 1.
            else:
                percent_of_path = (
                    (time_after_last_shot / self.RECOIL_RECOVERY_TIME)
                )
                percent_of_path = max(min(percent_of_path, 1.), .0)
            if percent_of_path >= 1.:
                self._recoil_zoom = self._DEFAULT_ZOOM
            _zoom_addition = (self._recoil_zoom - self._DEFAULT_ZOOM)
            zoom = (
                self._DEFAULT_ZOOM + (_zoom_addition * (1. - percent_of_path))
            )

            render_object.zoom(zoom, zoom)
            # ###########

            if self._trigger_is_pulled:
                # Курок спущен.
                cooldown = (60. / self.RATE_OF_FIRE)
                if time_after_last_shot > cooldown:
                    self.take_a_shot(st)

            return render_object

    class Melee(Gun):

        """
        Рукопашка. Если нет оружия.
        """

        DAMAGE_COEFFICIENT = .3
        AUTOMATIC = False
        RATE_OF_FIRE = 70.
        TIME_TO_ONE_SHOT = .2
        _DEFAULT_ZOOM = 1.3

        # Пока Владя не найдёт картинку кулака,
        # будем тыкать пистолей в свиблушко оппоненту.
        # TODO: Найти картинку кулака.
        _picture = "RenPyShooterPictures/sg_revolver.png"  # tmp
        _fire_picture = Null()
        _fire_sound = "RenpyShooterAudio/fist_punch.wav"

    class Revolver(Gun):

        DAMAGE_COEFFICIENT = 1.2
        AUTOMATIC = False
        RATE_OF_FIRE = 100.
        TIME_TO_ONE_SHOT = .1

        CAPACITY = 6

        RELOAD_TIME = 5.

        _picture = "RenPyShooterPictures/sg_revolver.png"
        _fire_picture = "RenPyShooterPictures/sg_revolver_shoot.png"
        _fire_sound = "RenpyShooterAudio/bullet_impact.wav"
        _no_bullet_sound = "RenpyShooterAudio/no_bullet.wav"

        _reload_hand_with_patrons = "RenPyShooterPictures/sg_reload_hand.png"
        _reload_gun_picture = "RenPyShooterPictures/sg_reload_gun.png"
        _bullet_picture = im.FactorScale(
            "RenPyShooterPictures/sg_reload_bullet.png",
            .4
        )
        _reload_sound = "RenpyShooterAudio/reload.wav"

        # Вероятность того, что при перезарядке не выпадет пуля.
        _reload_success_percent = .9
        _bullet_drop_start_coors = (
            # Абсолютные координаты пуль относительно '_reload_gun_picture'.
            # anchor на (.5, .5)
            (157, 315),
            (145, 351),
            (105, 359),
            (82, 337),
            (95, 309),
            (124, 293)
        )
        # Координаты пули, при зарядке её в "магазин",
        # относительно '_reload_hand_with_patrons'
        _bullet_reload_coor = (600, 90)

        def __init__(self, *args, **kwargs):
            super(Revolver, self).__init__(*args, **kwargs)

            # Заряжаемая в данный момент пуля.
            self._current_bullet = None
            self._drop_bullets = []

        def visit(self):
            result = super(Revolver, self).visit()
            result.extend(self._drop_bullets)
            if self._current_bullet:
                result.append(self._current_bullet)
            return result

        def _drop_bullet_action(self):
            pass

        def _reload_render(self, *rend_args):

            """
            Для револьвера особая перезарядка.
            """

            width, height, st, at = rend_args

            gun_hand_rend = renpy.render(
                self.reload_gun_picture,
                *rend_args
            )
            bullet_hand_rend = renpy.render(
                self.reload_hand_with_patrons,
                *rend_args
            )
            render_object = renpy.Render(
                (gun_hand_rend.width + bullet_hand_rend.width),
                max(gun_hand_rend.height, bullet_hand_rend.height)
            )
            render_object.blit(
                gun_hand_rend,
                (
                    int((render_object.width - gun_hand_rend.width)),
                    int((render_object.height - gun_hand_rend.height))
                )
            )

            if self._current_state == self.NEED_RELOAD_STATE:
                # Заряжяем патроны по одному.
                if self.CAPACITY is not None:
                    if self._current_capacity >= self.CAPACITY:
                        # Магазин заряжен.
                        self._patrons = []
                        self._drop_bullets = []
                        self._reload_anim = TimeTransform()
                        self._current_state = self.OK_STATE
                    elif self.shooter._action:
                        # Продолжаем заряжать. Магазин неполон.
                        if not self._reload_anim._is_changing():
                            # Поднимаем руку с пулей.
                            self._current_bullet = TimeTransform(
                                self.bullet_picture,
                                rotate=56
                            )
                            x = 0
                            y = render_object.height - bullet_hand_rend.height
                            x, y = map(int, (x, y))
                            self._reload_anim = TimeTransform(
                                pos=tuple(map(int, (x, render_object.height)))
                            )
                            self._reload_anim._st = st
                            self._reload_anim.change_values_over_time(
                                ((self.RELOAD_TIME / self.CAPACITY) / 2.),
                                ypos=y,
                                callback=renpy.partial(
                                    setattr,
                                    self,
                                    "_current_state",
                                    self.RELOAD_STATE1
                                )
                            )
                        # Отрисовка руки и заряжаемой пули.
                        render_object.blit(
                            bullet_hand_rend,
                            self._reload_anim.state.pos
                        )
                        if self._current_bullet:
                            x, y = self._bullet_reload_coor
                            # Сдвиг относительно размещения картинки.
                            xoffset, yoffset = self._reload_anim.state.pos
                            x += xoffset
                            y += yoffset
                            x, y = map(int, (x, y))
                            self._current_bullet._set_params(pos=(x, y))

                            bullet_rend = renpy.render(
                                self._current_bullet,
                                *rend_args
                            )
                            # anchor (.5, .5)
                            x -= (bullet_rend.width * .5)
                            y -= (bullet_rend.height * .5)
                            x, y = map(int, (x, y))
                            render_object.blit(bullet_rend, (x, y))

                else:
                    # Магазин бесконечный, но метод был вызван.
                    self._bullets = []
                    self._patrons = []
                    self._reload_anim = TimeTransform()
                    self._current_state = self.OK_STATE

            elif self._current_state == self.RELOAD_STATE1:
                # Заряжаем и возвращаемся за следующим.
                if self._current_bullet:
                    if self._reload_success_percent > random.random():
                        # Пуля заряжена успешно.
                        self._play_reload_sound()
                        self._bullets.append(self._current_bullet)
                    else:
                        # Криворукий стрелок выронил пулю.
                        self._drop_bullet_action()
                        self._drop_bullets.append(self._current_bullet)
                    self._current_bullet = None
                if not self._reload_anim._is_changing():
                    # Опускаем руку.
                    self._reload_anim.change_values_over_time(
                        ((self.RELOAD_TIME / self.CAPACITY) / 2.),
                        ypos=int(render_object.height),
                        callback=renpy.partial(
                            setattr,
                            self,
                            "_current_state",
                            self.NEED_RELOAD_STATE
                        )
                    )
                render_object.blit(
                    bullet_hand_rend,
                    self._reload_anim.state.pos
                )
            else:
                raise NotImplementedError(
                    __("Рендер состояния {0} не определён.").format(
                        self._current_state
                    )
                )

            for patron, (x, y) in zip(
                self._patrons[:],
                self._bullet_drop_start_coors
            ):
                if not patron._is_changing():
                    xoffset = render_object.width - gun_hand_rend.width
                    yoffset = render_object.height - gun_hand_rend.height
                    x += xoffset
                    y += yoffset
                    x, y = map(int, (x, y))
                    patron._st = st
                    patron._set_params(rotate=(-30), pos=(x, y))
                    patron.change_values_over_time(
                        random.uniform(.3, .5),
                        ypos=int((y + render_object.height)),
                        rotate=random.randint((-359), 359),
                        warper=lambda a: (a ** 2.),
                        callback=renpy.partial(
                            self._patrons.remove,
                            patron
                        )
                    )
                patron_render = renpy.render(patron, *rend_args)
                xpos, ypos = patron.state.pos
                x = xpos - (patron_render.width * .5)
                y = ypos - (patron_render.height * .5)
                x, y = map(int, (x, y))
                render_object.blit(patron_render, (x, y))

            for patron in self._drop_bullets[:]:
                if not patron._is_changing():
                    new_x = patron.state.xpos + random.uniform(.0, 300.)
                    new_y = patron.state.ypos + render_object.height
                    patron.change_values_over_time(
                        random.uniform(.3, .5),
                        pos=tuple(map(int, (new_x, new_y))),
                        rotate=random.randint((-359), 359),
                        warper=lambda a: (a ** 2.5),
                        callback=renpy.partial(
                            self._drop_bullets.remove,
                            patron
                        )
                    )
                patron_render = renpy.render(patron, *rend_args)
                x = patron.state.xpos - (patron_render.width * .5)
                y = patron.state.ypos - (patron_render.height * .5)
                x, y = map(int, (x, y))
                render_object.blit(patron_render, (x, y))

            return render_object

    class P2000(Gun):

        DAMAGE_COEFFICIENT = 1.
        AUTOMATIC = False
        RATE_OF_FIRE = 200.
        TIME_TO_ONE_SHOT = .1

        CAPACITY = 8

        _picture = "RenPyShooterPictures/mg_p2000.png"
        _fire_picture = "RenPyShooterPictures/mg_p2000_shoot.png"
        _fire_sound = "RenpyShooterAudio/bullet_impact.wav"
        _no_bullet_sound = "RenpyShooterAudio/no_bullet.wav"
        _reload_sound = "RenpyShooterAudio/reload.wav"

    class AK47(Gun):

        DAMAGE_COEFFICIENT = 1.5
        AUTOMATIC = True
        RATE_OF_FIRE = 600.
        TIME_TO_ONE_SHOT = .1

        CAPACITY = 30

        _picture = "RenPyShooterPictures/mg_ak47.png"
        _fire_picture = TimeTransform(
            "RenPyShooterPictures/shoot_ak47pic.png",
            anchor=(.5, .5),
            pos=(440, 321),
            rotate=0
        )
        _fire_sound = "RenpyShooterAudio/shoot_ak47.wav"
        _no_bullet_sound = "RenpyShooterAudio/no_bullet.wav"
        _reload_sound = "RenpyShooterAudio/reload.wav"
