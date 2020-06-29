﻿
label start:

    shooter:
        background "panorama.jpg"  # Фон. <Обязательно>
        player_gun _shooter.Revolver # Класс оружия игрока. <Опционально. Если нет - рукопашка.>
        player_gun_AUTOMATIC True  # Доп параметры оружия игрока. <Опционально>
        player_ARMOR_COEFFICIENT .8  # Доп параметры самого игрока. <Опционально>
        _hide_after_action False  # Скрыть поле боя автоматически. <Опционально. Умолчание - True.>
        success_action NullAction()  # Экшены на победу и поражение. <Опционально>
        failed_action MainMenu(False)
        enemy:  # Блок описания врага. Множественный аргумент. <Опционально. (Если ни одного - бой завершится не начавшись.)>
            _multiply 7  # Количество врагов, которые будут инициализированы с аргументами ниже. <Опционально. Умолчание - 1.>
            sprite "enemies/enemy_sprite.png"  # Спрайт врага. <Обязательно> (ImageBase only)
            damage_mask "enemies/enemy_sprite_damage_mask.png"  # Маска повреждений. Подробный док в 'EnemySprite'. <Обязательно>
            flash_picture "RenPyShooterPictures/flash.png"  # Спрайт выстрела противника. <Опционально>
            flash_picture_zoom .15  # Параметры 'flash_picture'. Передавать с префиксом 'flash_picture_'. <Опционально>
            flash_picture_pos (84, 768)
            flash_picture_anchor (.5, .5)
            gun None  # То же, что и 'player_gun', но для противника.
            gun_DAMAGE_COEFFICIENT .4  # То же, что и 'player_gun_', но для противника.
            enemy_AGRESSIVE .1  # То же, что и 'player_', но для противника.
        enemy:
            _multiply 2
            sprite "enemies/enemy_sprite.png"
            damage_mask "enemies/enemy_sprite_damage_mask.png"
            flash_picture "RenPyShooterPictures/flash.png"
            flash_picture_zoom .15
            flash_picture_pos (84, 768)
            flash_picture_anchor (.5, .5)
            gun _shooter.P2000
            enemy_AGRESSIVE .05

    "Сначала у меня был ствол, но теперь нет даже его. Придётся кулаками."

    shooter:  # Параметров по минимуму.
        background "panorama.jpg"
        enemy:
            sprite "enemies/enemy_sprite.png"
            damage_mask "enemies/enemy_sprite_damage_mask.png"
            enemy_AGRESSIVE 1.  # Совсем злобный чёрт.

    return