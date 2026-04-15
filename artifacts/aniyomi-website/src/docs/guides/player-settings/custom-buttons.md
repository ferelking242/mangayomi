---
title: Custom buttons
titleTemplate: Player settings
description: Edit and create custom buttons.
---

<script setup>
import TitleIcon from "@theme/components/TitleIcon.vue";
</script>

# Custom buttons

This sections deals with custom buttons and how they work.

::: warning
This page explores some advanced features.
:::

## What are custom buttons?

Custom buttons provides a way to execute lua code by pressing a button in the player. Watchtower also provides an interface to interact with some parts of the player. By default, Watchtower comes with a button to seek 85 seconds forward which is meant to skip intros. The duration can be changed by long pressing the button.

## Adding a custom button

To add a custom button, press the `Add` button in the bottom right. A button must have a unique title, as long with some lua code that will be executed when pressed. Additionally, the custom button may include some code that will be executed when long pressed, and code that will be executed once on player startup.

## Editing a custom button

The up or down arrow will the determine the order of the custom buttons. Press the <TitleIcon name="custom_button_star"/>button to set a button as the primary one, <TitleIcon name="custom_button_edit"/>to edit a custom button, and <TitleIcon name="custom_button_delete"/>to delete a custom button.

::: warning For your information
Only one button can be set as a primary, which will appear in the player. The rest will appear in the [More](/docs/guides/video-player/sheets#more-sheet) sheet.
:::

## Examples

::: details +85 s
This one is added in as default. Tapping the custom button will seek ahead by the skip intro length, and long pressing will change the intro length for the anime.

**Lua code**:
```lua
local intro_length = mp.get_property_number("user-data/current-anime/intro-length")
watchtower.seek_by(intro_length)
```

**Lua code (on long press)**:
```lua
watchtower.int_picker("Change intro length", "%ds", 0, 255, 1, "user-data/current-anime/intro-length")
```

**On startup**:
```lua
function update_button(_, length)
  if length ~= nil then
    if length == 0 then
      watchtower.hide_button()
      return
    else
      watchtower.show_button()
    end
    watchtower.set_button_title("+" .. length .. " s")
  end
end

if $isPrimary then
  mp.observe_property("user-data/current-anime/intro-length", "number", update_button)
end
```
  :::

::: details Toggle debanding
This button will toggle debanding when pressed, and will open up a picker to choose the deband threshold on long press.

**Lua code**:
```lua
local deband = mp.get_property_bool("deband")
mp.set_property_bool("deband", not deband)
watchtower.show_text("Debanding: " .. (deband and "off" or "on"))
```

**Lua code (on long press)**:
```lua
watchtower.int_picker("Change deband threshold", "%d", 0, 4096, 4, "deband-threshold")
```
  :::

## Advanced

Internally, buttons are dispatched through `mp.register_script_message()` with the name `call_button_<id>` and `call_button_<id>_long` where `<id>` is the button id (it is shown in the top right when editing a button). This means they can be invoked through a keybind for example. If `Double tap (center)` is set to `custom` under <nav to="gestures">, then `0x10002 script-message call_button_1_long` will invoke the long press of the custom button with id 1.

Additionally, `$id` can be used as a placeholder in a custom button for its own id, and `$isPrimary` will result in a boolean whether the current button is the primary one. This can be useful if you only want to execute some code on startup if it's the primary one, see +85s for an example.

## Lua interface

Watchtower provides a lua interface that can be used both in custom buttons and in lua scripts.

### `watchtower.show_text(text)`

Display some [Text](/docs/guides/video-player/#auto-play-is-off) on the player.

* `text` (string) - The text to display.

### `watchtower.hide_ui()`

Hide the ui.

### `watchtower.show_ui()`

Show the ui.

### `watchtower.toggle_ui()`

Toggle the visibility of the ui.

### `watchtower.show_subtitle_settings()`

Show the [Subtitle settings](/docs/guides/video-player/panels#subtitle-settings) panel.

### `watchtower.show_subtitle_delay()`

Show the [Subtitle delay](/docs/guides/video-player/panels#subtitle-delay) panel.

### `watchtower.show_audio_delay()`

Show the [Audio delay](/docs/guides/video-player/panels#audio-delay) panel.

### `watchtower.show_video_filters()`

Show the [Video filters](/docs/guides/video-player/panels#video-filters) panel.

### `watchtower.show_software_keyboard()`

Show a keyboard on screen.

### `watchtower.hide_software_keyboard()`

Hide the on-screen keyboard.

### `watchtower.toggle_software_keyboard()`

Toggle the visibility of the on-screen keyboard.

### `watchtower.set_button_title(text)`

Set the title of the custom button.

* `text` (string) - The text to set the button to.

### `watchtower.reset_button_title()`

Reset the custom button title.

### `watchtower.hide_button()`

Hide the primary button from the player.

### `watchtower.show_button()`

Show the primary button.

### `watchtower.toggle_button()`

Toggle the visibility of the primary button.

### `watchtower.previous_episode()`

Switch to the previous episode.

### `watchtower.next_episode()`

Switch to the next episode.

### `watchtower.pause()`

Pause the player.

### `watchtower.unpause()`

Resume the player.

### `watchtower.pauseunpause()`

Toggle pausing.

### `watchtower.seek_by(value)` {#watchtower-seek-by-value}

Seek relative by a value. Enter a negative number to seek backwards.

* `value` (integer) - Seconds to seek by.

### `watchtower.seek_to(value)` {#watchtower-seek-to-value}

Seek to a position.

* `value` (integer) - Position to seek to (in seconds).

### `watchtower.seek_by_with_text(value, text)`

Like [seek_by](#watchtower-seek-by-value), but display some text in the seek ripple.

* `value` (integer) - Seconds to seek by.
* `text` (string) - Text to display.

### `watchtower.seek_to_with_text(value, text)`

Like [seek_to](#watchtower-seek-to-value), but display some text in the seek ripple.

* `value` (integer) - Position to seek to (in seconds).
* `text` (string) - Text to display.

### `watchtower.int_picker(title, name_format, start, stop, step, property)`

Open up a wheel picker to set an integer value to a property.

* `title` (string) - Title of the dialog.
* `name_format` (string) - Format of each entry. Set to `%d` to just display the number.
* `start` (integer) - Start value for integer range.
* `stop` (integer) - Stop value for integer range.
* `step` (integer) - Step value for integer range.
* `property` (string) - mpv property to assign value to.
