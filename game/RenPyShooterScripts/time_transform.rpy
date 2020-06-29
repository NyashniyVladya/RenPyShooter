
init -8 python in _shooter:

    class TimeTransform(Transform):

        """
        Транса с изменениями значений в течении времени.
        (Более лёгкая версия старого 'MoveEventer'.)
        """

        def __init__(self, *args, **kwargs):

            super(TimeTransform, self).__init__(*args)
            self._set_params(**kwargs)

            self._st = .0
            self._start_time = None
            self._end_time = None
            self._changes = None
            self._warper = None
            self._callback = None

        def _get_state_diff_from_mapping(self, **_mapping):
            """
            Возвращает разницу между значениями из маппинга
            и текущими значениями 'self.state'.
            Возвращает словарь формата:
                {
                    "имя значения state":
                        (текущее_значение, новое_значение),
                    ...
                }
            """
            result = {}
            for k, v in _mapping.iteritems():
                if not hasattr(self.state, k):
                    continue
                current_value = getattr(self.state, k)
                if current_value == v:
                    continue
                result[k] = (current_value, v)
            return result

        def change_values_over_time(self, delay, **_new_values):

            """
            Изменяет значения на переданные в течении 'delay' секунд.
            """

            warper = _new_values.pop("warper", "linear")
            if not callable(warper):
                warper = renpy.atl.warpers[warper]

            callback = _new_values.pop("callback", None)

            need_changes = self._get_state_diff_from_mapping(**_new_values)
            if not need_changes:
                if callable(callback):
                    callback()
                return

            self._start_time = self._st
            self._end_time = self._start_time + max(float(delay), .0)
            self._changes = need_changes
            self._warper = warper
            self._callback = callback

        def _set_state_periodic(self, st):
            """
            Метод для периодического вызова в цикле рендера.
            """
            if not self._changes:
                return
            past_time = st - self._start_time
            delay = self._end_time - self._start_time
            if delay > .0:
                completed = past_time / delay
            else:
                completed = 1.
            _new_values = {}
            for k, (old_value, new_value) in self._changes.iteritems():
                value = self.interpolate(
                    self._warper(completed),
                    old_value,
                    new_value
                )
                _new_values[k] = value
            self._set_params(**_new_values)
            if completed >= 1.:
                if callable(self._callback):
                    self._callback()
                self._stop_changes()

        def _is_changing(self):
            """
            Происходят ли изменения в данный момент.
            """
            return bool(self._changes)

        def _stop_changes(self):
            self._start_time = None
            self._end_time = None
            self._changes = None
            self._warper = None
            self._callback = None

        def _set_params(self, **_params):
            need_changes = self._get_state_diff_from_mapping(**_params)
            if not need_changes:
                return
            for k, (old_value, new_value) in need_changes.iteritems():
                setattr(self.state, k, new_value)

        def render(self, width, height, st, at):
            self._st = st
            self._set_state_periodic(st)
            rend = super(TimeTransform, self).render(width, height, st, at)
            renpy.redraw(self, .0)
            return rend

        @staticmethod
        def interpolate(t, a, b, _type=None):
            """
            Линейная интерполяция.　Небольшая ATL обёртка.
            :t:
                Процент прошедшего времени.
                .0 <= t <= 1.
            :a:
                Значение "до".
            :b:
                Значение "после"
            :_type:
                Тип приведения. По умолчанию - тип значения 'b'.
            """
            if not isinstance(_type, (type, tuple)):
                _type = type(b)
                if _type is tuple:
                    _type = tuple(map(type, b))
            t = max(min(t, 1.), .0)
            return renpy.atl.interpolate(t, a, b, _type)
