-- Capture focused Solomon's Key events from deterministic controller input.

local output_path = assert(os.getenv("SOLOMON_RUNTIME_TRACE"))
local scenario = assert(os.getenv("SOLOMON_RUNTIME_SCENARIO"))
local max_frames = assert(tonumber(os.getenv("SOLOMON_RUNTIME_MAX_FRAMES")))
local input_spec = os.getenv("SOLOMON_RUNTIME_INPUTS") or ""
local patch_spec = os.getenv("SOLOMON_RUNTIME_PATCHES") or ""
local output = assert(io.open(output_path, "w"))
local audio_probe = scenario == "audio-channel-priority"
local pause_probe = scenario == "room-1-pause-resume"
local death_probe = scenario == "room-1-life-loss-reload"

local function symbol(name)
    local address = debugger.getsymboloffset(name)
    assert(address ~= nil and address >= 0, "missing debugger symbol: " .. name)
    return address
end

local ram = {
    thread = symbol("ThreadIndex"),
    joypad = symbol("Joypad1Raw"),
    room = symbol("CurrentRoomIndex"),
    gameplay_updates = symbol("GameplayUpdateCount"),
    timer = symbol("TimerDecrementStep"),
    mirror = symbol("RoomItemRuntimeData"),
    map = symbol("RoomMap"),
    dana = symbol("DanaObject"),
    fireball = symbol("FireballObject"),
    fireball_active = symbol("FireballActive"),
    audio_state = symbol("AudioChannelState"),
    audio_active = symbol("AudioActiveChannelMask"),
    audio_pointer = symbol("TempPointer08"),
    audio_hardware_index = symbol("TempPointer08") + 2,
    game_state = symbol("GameStateFlags"),
    remaining_lives = symbol("RemainingLives"),
}

local function byte(address)
    return memory.readbyte(address)
end

local function word(address)
    return byte(address) + 0x100 * byte(address + 1)
end

local function timer_digits()
    return string.format(
        "%02X%02X%02X%02X",
        byte(ram.timer + 3),
        byte(ram.timer + 4),
        byte(ram.timer + 5),
        byte(ram.timer + 6))
end

local function emit(event, detail)
    output:write(string.format(
        "%d,%s,%s,%02X,%02X,%s,%02X,%02X,%02X,%02X\n",
        emu.framecount(), event, detail or "", byte(ram.thread), byte(ram.room),
        timer_digits(), byte(ram.dana + 7), byte(ram.dana + 10),
        byte(ram.mirror + 11), byte(ram.remaining_lives)))
    output:flush()
end

local seen = {}
local function emit_once(event, detail)
    if seen[event] then
        return
    end
    seen[event] = true
    emit(event, detail)
end

local hooks = {
    {"NMI", "first_nmi"},
    {"ReadJoyPads", "first_joypad_read"},
    {"SwitchThreads", "first_thread_switch"},
    {"RoomLoadThread", "room_load"},
    {"PrepareRoomIntro", "room_intro"},
    {"MainGameplayThread", "gameplay_start"},
    {"PauseGameThread", "pause_thread", true},
    {"RunDanaDeathTransition", "dana_death", true},
    {"FinishDanaDeathAnimation", "death_animation_finished", true},
    {"FinalizeGameplayExit", "gameplay_exit", true},
    {"ReloadRoomAfterLifeLoss", "life_loss_reload", true},
    {"DecrementTimer", "first_timer_tick"},
    {"UpdateDanaControlState", "dana_control", true},
    {"UpdateObjectMotionAndCollision", "object_motion", true},
    {"SampleObjectRoomMapCollision", "object_collision", true},
    {"RunEnemyAiDispatcher", "enemy_ai", true},
    {"TryStartBlockMagicAction", "block_magic_request", true},
    {"CreateBlockInRoomMap", "block_created", true},
    {"CastFireballFromInventory", "fireball_cast", true},
    {"ActivateFireball", "fireball_activated", true},
    {"UpdateActiveFireballCollision", "fireball_collision", true, "fireball_activated"},
    {"UpdateFireballLifetime", "fireball_lifetime", true, "fireball_activated"},
    {"CheckInactiveFireballCleanup", "fireball_cleanup", true, "fireball_activated"},
    {"EnterRoomDoor", "door_entered", true},
    {"RoomClearThread", "room_clear", true},
    {"SubtractTimerBy8", "room_bonus_tick", true},
}

local scheduler_sample_count = 0
local timer_sample_count = 0
local gameplay_start_frame = nil
local scheduler_window_counts = {0, 0, 0, 0, 0, 0, 0, 0}
local timer_window_calls = 0
local timer_window_frames = {}
local timer_window_ticks = 0
local timer_window_initial_ticks = nil
local timer_window_steady_max_ticks = 0
local gameplay_update_window_count = 0
local gameplay_skip_window_count = 0
local pause_active = false
local pause_cleared = false
for _, hook in ipairs(hooks) do
    local routine = hook[1]
    local event = hook[2]
    local requires_gameplay = hook[3]
    local prerequisite = hook[4]
    memory.registerexecute(symbol(routine), function()
        if routine == "MainGameplayThread" and gameplay_start_frame == nil then
            gameplay_start_frame = emu.framecount()
        end
        if routine == "RoomLoadThread" and seen["room_load"] then
            emit_once("next_room_load", routine)
        elseif (not requires_gameplay or seen["gameplay_start"])
            and (prerequisite == nil or seen[prerequisite]) then
            emit_once(event, routine)
        end
        if routine == "SwitchThreads" and seen["gameplay_start"]
            and scheduler_sample_count < 24 then
            emit("scheduler_switch", string.format("%02X", byte(ram.thread)))
            scheduler_sample_count = scheduler_sample_count + 1
        end
        if routine == "SwitchThreads" and gameplay_start_frame ~= nil
            and emu.framecount() < gameplay_start_frame + 60 then
            local context = byte(ram.thread)
            scheduler_window_counts[context + 1] = scheduler_window_counts[context + 1] + 1
        end
        if routine == "DecrementTimer" and seen["gameplay_start"]
            and timer_sample_count < 8 then
            emit("timer_sample", timer_digits())
            timer_sample_count = timer_sample_count + 1
        end
        if routine == "DecrementTimer" and gameplay_start_frame ~= nil
            and emu.framecount() < gameplay_start_frame + 60 then
            local pending_ticks = byte(ram.gameplay_updates)
            timer_window_calls = timer_window_calls + 1
            timer_window_frames[emu.framecount()] = true
            timer_window_ticks = timer_window_ticks + pending_ticks
            if timer_window_initial_ticks == nil then
                timer_window_initial_ticks = pending_ticks
            elseif pending_ticks > timer_window_steady_max_ticks then
                timer_window_steady_max_ticks = pending_ticks
            end
        end
        if pause_probe and routine == "UpdateDanaControlState" then
            if pause_active then
                emit_once("gameplay_during_pause", routine)
            elseif pause_cleared then
                emit_once("gameplay_resumed", routine)
            end
        end
    end)
end

local audio_current_command = 0
local audio_routes = {}
if audio_probe then
    memory.registerexecute(symbol("StartQueuedSoundEffect"), function()
        if emu.framecount() >= 700 then
            audio_current_command = memory.getregister("y") or 0
            emit(
                "audio_command_start",
                string.format(
                    "slot=%d;command=%02X",
                    memory.getregister("x") or 0,
                    audio_current_command))
        end
    end)

    memory.registerexecute(symbol("InitializeSoundEffectChannel"), function()
        if emu.framecount() >= 700 then
            local descriptor = word(ram.audio_pointer)
            local offset = memory.getregister("y") or 0
            local virtual_channel = memory.getregister("a") or 0
            local stream = word(descriptor + offset + 1)
            emit(
                "audio_virtual_start",
                string.format(
                    "command=%02X;virtual=%d;stream=%04X",
                    audio_current_command,
                    virtual_channel,
                    stream))
        end
    end)

    memory.registerexecute(symbol("WriteCurrentApuChannel"), function()
        if emu.framecount() >= 700 then
            local hardware_index = byte(ram.audio_hardware_index)
            local apu_channel = 3 - hardware_index
            local pointer = word(ram.audio_pointer)
            local virtual_channel = math.floor(
                (pointer - ram.audio_state) / 0x10)
            if audio_routes[apu_channel] ~= virtual_channel then
                audio_routes[apu_channel] = virtual_channel
                emit(
                    "audio_route",
                    string.format(
                        "apu=%d;virtual=%d;mask=%02X",
                        apu_channel,
                        virtual_channel,
                        byte(ram.audio_active)))
            end
        end
    end)
end

memory.registerexecute(symbol("SkipNmiGameplayServicesForStack"), function()
    if gameplay_start_frame ~= nil
        and emu.framecount() < gameplay_start_frame + 60 then
        gameplay_skip_window_count = gameplay_skip_window_count + 1
    end
end)

memory.registerwrite(ram.gameplay_updates, 1, function(address, size, value)
    if gameplay_start_frame ~= nil
        and emu.framecount() < gameplay_start_frame + 60
        and value ~= 0 then
        gameplay_update_window_count = gameplay_update_window_count + 1
    end
end)

memory.registerwrite(ram.game_state, 1, function(address, size, value)
    if not pause_probe or not seen["pause_thread"] then
        return
    end
    if bit.band(value, 0x04) ~= 0 and not pause_active then
        pause_active = true
        emit_once("pause_active", string.format("%04X=%02X", address, value))
    elseif pause_active and bit.band(value, 0x04) == 0 then
        pause_active = false
        pause_cleared = true
        emit_once("pause_cleared", string.format("%04X=%02X", address, value))
    end
end)

memory.registerwrite(ram.remaining_lives, 1, function(address, size, value)
    if death_probe and seen["dana_death"] then
        emit_once("life_decremented", string.format("%04X=%02X", address, value))
    end
end)

memory.registerwrite(ram.map, 192, function(address, size, value)
    if seen["block_magic_request"] then
        emit_once(
            "room_map_write",
            string.format("%04X=%02X", address, value))
    end
end)

memory.registerwrite(ram.fireball_active, 1, function(address, size, value)
    if seen["fireball_activated"] and value == 0 then
        emit_once("fireball_deactivated", string.format("%04X=%02X", address, value))
    end
end)

memory.registerwrite(ram.fireball, 1, function(address, size, value)
    if seen["fireball_activated"] and value == 0 then
        emit_once("fireball_retired", string.format("%04X=%02X", address, value))
    end
end)

local input_ranges = {}
for first, last, buttons in string.gmatch(input_spec, "(%d+)%-(%d+):([^;]+)") do
    table.insert(input_ranges, {
        first = tonumber(first),
        last = tonumber(last),
        buttons = buttons,
    })
end

local patches = {}
for frame, name, offset, operation, value, reason in string.gmatch(
    patch_spec, "(%d+),([^,]+),(%d+),([^,]+),(%d+),([^;]+)") do
    table.insert(patches, {
        frame = tonumber(frame),
        address = symbol(name) + tonumber(offset),
        operation = operation,
        value = tonumber(value),
        reason = reason,
        applied = false,
    })
end

local function apply_due_patches(frame)
    for _, patch in ipairs(patches) do
        if not patch.applied and frame >= patch.frame then
            local previous = byte(patch.address)
            local value = patch.value
            if patch.operation == "or" then
                value = bit.bor(previous, value)
            end
            memory.writebyte(patch.address, value)
            emit(
                "controlled_patch",
                string.format(
                    "%04X:%02X>%02X:%s",
                    patch.address, previous, value, patch.reason))
            patch.applied = true
        end
    end
end

local function controller_for_frame(frame)
    local state = {}
    for _, range in ipairs(input_ranges) do
        if frame >= range.first and frame <= range.last then
            for button in string.gmatch(range.buttons, "[^+]+") do
                if button == "a" or button == "b" then
                    state[string.upper(button)] = true
                else
                    state[button] = true
                end
            end
        end
    end
    return state
end

output:write(
    "frame,event,detail,thread,room,timer,dana_y,dana_x,active_enemies,remaining_lives\n")
emit("trace_start", scenario)

local previous_dana_x = byte(ram.dana + 10)
while emu.framecount() < max_frames do
    joypad.set(1, controller_for_frame(emu.framecount()))
    emu.frameadvance()
    apply_due_patches(emu.framecount())
    local current_dana_x = byte(ram.dana + 10)
    if bit.band(byte(ram.joypad), 0x01) ~= 0 then
        emit_once("right_input_seen", "Joypad1Raw")
    end
    if bit.band(byte(ram.joypad), 0x40) ~= 0 then
        emit_once("b_input_seen", "Joypad1Raw")
    end
    if bit.band(byte(ram.joypad), 0x80) ~= 0 then
        emit_once("a_input_seen", "Joypad1Raw")
    end
    if bit.band(byte(ram.joypad), 0x10) ~= 0 then
        emit_once("start_input_seen", "Joypad1Raw")
    end
    if seen["right_input_seen"] and current_dana_x ~= previous_dana_x then
        emit_once(
            "dana_horizontal_move",
            string.format("%02X>%02X", previous_dana_x, current_dana_x))
    end
    previous_dana_x = current_dana_x
end

if gameplay_start_frame ~= nil then
    local scheduler_parts = {}
    for context = 0, 7 do
        table.insert(
            scheduler_parts,
            string.format("%d=%d", context, scheduler_window_counts[context + 1]))
    end
    local distinct_timer_frames = 0
    for _, _ in pairs(timer_window_frames) do
        distinct_timer_frames = distinct_timer_frames + 1
    end
    emit("scheduler_window", table.concat(scheduler_parts, ";"))
    emit(
        "timer_window",
        string.format(
            "calls=%d;frames=%d;updates=%d;skips=%d;ticks=%d;initial=%d;steady=%d;queued=%d;max=%d",
            timer_window_calls,
            distinct_timer_frames,
            gameplay_update_window_count,
            gameplay_skip_window_count,
            timer_window_ticks,
            timer_window_initial_ticks or 0,
            timer_window_ticks - (timer_window_initial_ticks or 0),
            gameplay_update_window_count
                - (timer_window_ticks - (timer_window_initial_ticks or 0)),
            timer_window_steady_max_ticks))
end

emit("trace_end", scenario)
output:close()
emu.exit()
