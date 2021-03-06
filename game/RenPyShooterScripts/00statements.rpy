
python early in _shooter_statements:

    import __builtin__
    import store

    class ShooterStatementParser(object):

        __author__ = "Vladya"

        BLOCK_NAME = "shooter"
        SHOOTER_BLOCK_STRUCT = {
            "arguments": (
                "background",
                "player_gun",
                "_hide_after_action",
                "_max_enemy_on_screen",
                "_enemies_pos",
                "success_action",
                "failed_action"
            ),
            "prefixes": ("player_gun_", "player_"),
            "required": ("background",),
            "subblocks": {
                "enemy": {
                    "arguments": (
                        "_multiply",
                        "sprite",
                        "damage_mask",
                        "flash_picture",
                        "gun"
                    ),
                    "prefixes": ("flash_picture_", "gun_", "enemy_"),
                    "required": ("sprite", "damage_mask"),
                    "subblocks": {}
                }
            }
        }

        @classmethod
        def execute_shooter_statement(cls, arg_dict):

            _raw_args = arg_dict.copy()
            arg_dict = cls._evaluate_args(arg_dict)

            success_action = arg_dict.pop("success_action", None)
            failed_action = arg_dict.pop("failed_action", None)
            _hide_after_action = arg_dict.pop("_hide_after_action", True)
            _max_enemy_on_screen = arg_dict.pop("_max_enemy_on_screen", None)
            _enemies_pos = arg_dict.pop("_enemies_pos", "random")
            for _del_raw in (
                "success_action",
                "failed_action",
                "_hide_after_action",
                "_max_enemy_on_screen",
                "_enemies_pos"
            ):
                _raw_args.pop(_del_raw, None)
            _battlefield = cls.get_battlefield_object_from_arg_dict(arg_dict)
            _battlefield._raw_args = _raw_args

            _battlefield_displayable = _battlefield._battlefield._child
            if isinstance(_max_enemy_on_screen, (int, float)):
                _m = _max_enemy_on_screen
                _battlefield_displayable.MAX_ENEMY_ON_SCREEN = _m

            b = __builtin__
            _arrays = (b.list, b.set, b.frozenset, b.tuple)
            if isinstance(_enemies_pos, basestring):
                if _enemies_pos not in ("random", "line_up"):
                    raise RuntimeError(
                        __("Некорректный параметр '_enemies_pos'.")
                    )
            elif isinstance(_enemies_pos, _arrays):
                for p in _enemies_pos:
                    if not isinstance(p, float):
                        raise RuntimeError(__("Передано не 'float' значение."))
            else:
                raise RuntimeError(__("Некорректный параметр '_enemies_pos'."))
            _battlefield_displayable.ENEMIES_POS = _enemies_pos

            roll_fw = renpy.roll_forward_info()
            renpy.show(
                _battlefield.GLOBAL_NAME,
                layer="master",
                what=_battlefield
            )
            _battlefield._start()
            result = ui.interact(suppress_window=True, roll_forward=roll_fw)
            _battlefield._pause()
            renpy.checkpoint(result)

            if result:
                renpy.run(success_action)
            else:
                renpy.run(failed_action)

            if _hide_after_action:
                renpy.hide(_battlefield.GLOBAL_NAME)

        @classmethod
        def get_battlefield_object_from_arg_dict(cls, arg_dict):

            arg_dict = arg_dict.copy()

            background = arg_dict.pop("background")
            player_gun = arg_dict.pop("player_gun", None)
            enemy_args = arg_dict.pop("enemy", [])
            player_gun_, player_, arg_dict = renpy.easy.split_properties(
                arg_dict,
                "player_gun_",
                "player_",
                ""
            )

            enemies = []
            for enemy_dict in enemy_args[:]:
                _multiply = enemy_dict.pop("_multiply", 1)
                sprite = enemy_dict.pop("sprite")
                damage_mask = enemy_dict.pop("damage_mask")
                flash_picture = enemy_dict.pop("flash_picture", None)
                gun = enemy_dict.pop("gun", None)
                gun_, enemy_, enemy_dict = renpy.easy.split_properties(
                    enemy_dict,
                    "gun_",
                    "enemy_",
                    ""
                )
                flash_picture_, enemy_dict = renpy.easy.split_properties(
                    enemy_dict,
                    "flash_picture_",
                    ""
                )
                flash_picture_ = dict(
                    map(
                        lambda x: ("flash_picture_{0}".format(x[0]), x[1]),
                        flash_picture_.iteritems()
                    )
                )
                for _i in xrange(_multiply):
                    enemy = store._shooter.Enemy(
                        sprite=sprite,
                        damage_mask=damage_mask,
                        flash_picture=flash_picture,
                        gun_class=gun,
                        **flash_picture_
                    )
                    for k, v in gun_.iteritems():
                        setattr(enemy.gun, k, v)
                    for k, v in enemy_.iteritems():
                        setattr(enemy, k, v)
                    enemies.append(enemy)

            _battlefield = store._shooter.BattleField(
                background,
                player_gun,
                *enemies
            )
            for k, v in player_gun_.iteritems():
                setattr(_battlefield._player_pov.gun, k, v)
            for k, v in player_.iteritems():
                setattr(_battlefield._player_pov, k, v)

            return _battlefield

        @classmethod
        def _evaluate_args(cls, arg_dict):
            """
            "Распаковывает" строки аргументов.
            """
            result = {}
            for k, v in arg_dict.iteritems():
                if isinstance(v, basestring):
                    v = renpy.python.py_eval(v)
                elif isinstance(v, list):
                    v = list(map(cls._evaluate_args, v))
                else:
                    raise TypeError(
                        __("Некорректный тип '{0}' ({1}).").format(type(v), k)
                    )
                result[k] = v
            return result

        @classmethod
        def parse_shooter_block(cls, l):
            kwargs = {
                "l": l,
                "block_name": cls.BLOCK_NAME
            }
            kwargs.update(cls.SHOOTER_BLOCK_STRUCT)
            return cls._parse_block(**kwargs)

        @staticmethod
        def _get_expression(l, arg_name):
            value = l.simple_expression()
            if value is None:
                msg = __("Не определено значение аргумента '{0}'.")
                msg = msg.format(arg_name)
                l.error(msg)
            return value

        @classmethod
        def _parse_block(
            cls,
            l,
            block_name,
            arguments,
            prefixes,
            required,
            subblocks
        ):

            """
            Возвращает словарь результатов парсинга.
            :l:
                Объект 'Lexer' для парсинга.
            :block_name:
                Имя блока который парсим.
            :arguments:
                Массив допустимых аргументов.
            :prefixes:
                Допустимые префиксы для аргументов.
            :required:
                Массив аргументов, которые обязательно должны быть в блоке.
            :subblocks:
                Словарь аргументов парсинга сабблоков, где ключи - имена,
                а значения - словари с ключами:
                    'arguments', 'prefixes', 'required' и 'subblocks'.
            """

            required_args = set()
            required_args.update(required)

            l.require(':')
            l.expect_eol()
            l.expect_block(block_name)
            l = l.subblock_lexer()

            result = {}
            while l.advance():

                argument = l.word()
                required_args.discard(argument)

                if l.has_block():
                    if argument in subblocks:
                        _subblock_parse_args = {
                            "l": l,
                            "block_name": argument,
                            "arguments": subblocks[argument]["arguments"],
                            "prefixes": subblocks[argument]["prefixes"],
                            "required": subblocks[argument]["required"],
                            "subblocks": subblocks[argument]["subblocks"]
                        }
                        result.setdefault(argument, []).append(
                            cls._parse_block(**_subblock_parse_args)
                        )
                    else:
                        msg = __("Блок '{0}' незадекларирован.")
                        msg = msg.format(argument)
                        l.error(msg)
                else:
                    if argument in arguments:
                        result[argument] = cls._get_expression(l, argument)
                    else:
                        for prefix in filter(argument.startswith, prefixes):
                            if argument == prefix:
                                continue
                            result[argument] = cls._get_expression(l, argument)
                            break
                        else:
                            msg = __("Неизвестный аргумент '{0}'.")
                            msg = msg.format(argument)
                            l.error(msg)

                    l.expect_eol()

            msg = __("Не передан обязательный аргумент '{0}' для блока '{1}'.")
            for argument in required_args:
                msg = msg.format(argument, block_name)
                l.error(msg)

            return result

    renpy.register_statement(
        name=ShooterStatementParser.BLOCK_NAME,
        block=True,
        parse=ShooterStatementParser.parse_shooter_block,
        execute=ShooterStatementParser.execute_shooter_statement,
        force_begin_rollback=True
    )
