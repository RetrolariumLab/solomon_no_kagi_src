-- Start the selected authored room through the original Solomon's Key engine.

local function required_integer(name, minimum, maximum)
    local raw = os.getenv(name)
    local value = tonumber(raw or "")
    if value == nil or value < minimum or value > maximum
            or math.floor(value) ~= value then
        error(name .. " must be an integer in range " .. minimum .. ".." .. maximum)
    end
    return value
end

local function optional_flag(name)
    local value = os.getenv(name)
    if value == nil or value == "" or value == "0" then
        return false
    end
    if value == "1" then
        return true
    end
    error(name .. " must be 0 or 1")
end

local requested_room = required_integer("SOLOMON_LEVEL_ROOM", 0, 52)
local room_load_address = required_integer(
    "SOLOMON_LEVEL_ROOM_LOAD_ADDRESS", 0x8000, 0xffff)
local gameplay_address = required_integer(
    "SOLOMON_LEVEL_GAMEPLAY_ADDRESS", 0x8000, 0xffff)
local current_room_address = required_integer(
    "SOLOMON_LEVEL_CURRENT_ROOM_ADDRESS", 0, 0x07ff)
local start_frame = required_integer("SOLOMON_LEVEL_START_FRAME", 1, 3598)
local ready_frames = required_integer(
    "SOLOMON_LEVEL_READY_FRAMES", start_frame + 2, 3600)
local exit_after_ready = optional_flag("SOLOMON_LEVEL_EXIT")
local result_path = os.getenv("SOLOMON_LEVEL_RESULT")

local room_load_count = 0
local gameplay_count = 0
local room_was_selected = false
local gameplay_ready = false
local transitions = {}

local function byte(address)
    return memory.readbyte(address)
end

local function record(event)
    transitions[#transitions + 1] = string.format(
        "%d:%s:%02x:%04x",
        emu.framecount(),
        event,
        byte(current_room_address),
        memory.getregister("pc"))
end

memory.registerexecute(room_load_address, function()
    room_load_count = room_load_count + 1
    if not room_was_selected then
        memory.writebyte(current_room_address, requested_room)
        room_was_selected = true
        record("room-selected")
    else
        record("room-reloaded")
    end
end)

memory.registerexecute(gameplay_address, function()
    gameplay_count = gameplay_count + 1
    if room_was_selected and byte(current_room_address) == requested_room then
        gameplay_ready = true
        if gameplay_count == 1 then
            record("gameplay-ready")
        end
    end
end)

local function write_result(status)
    if result_path == nil or result_path == "" then
        return
    end
    local output = assert(io.open(result_path, "w"))
    output:write(string.format(
        "status=%s requested_room=%02x current_room=%02x "
            .. "room_loads=%d gameplay_hits=%d frame=%d pc=%04x\n",
        status,
        requested_room,
        byte(current_room_address),
        room_load_count,
        gameplay_count,
        emu.framecount(),
        memory.getregister("pc")))
    output:write("trace=" .. table.concat(transitions, ",") .. "\n")
    output:close()
end

local start_released = false
for frame = 0, ready_frames do
    if frame == start_frame or frame == start_frame + 1 then
        joypad.set(1, {start = true})
    else
        joypad.set(1, {})
        if frame > start_frame + 1 then
            start_released = true
        end
    end
    emu.frameadvance()
    if gameplay_ready and start_released then
        break
    end
end

joypad.set(1, {})
if not room_was_selected then
    write_result("room-load-timeout")
    if exit_after_ready then
        emu.exit()
    end
    error("Solomon's Key did not enter RoomLoadThread")
end
if not gameplay_ready then
    write_result("gameplay-timeout")
    if exit_after_ready then
        emu.exit()
    end
    error("Solomon's Key did not enter MainGameplayThread for the selected room")
end

write_result("ready")
gui.addmessage(string.format(
    "Level Studio: Room %02d ready", requested_room + 1))
if exit_after_ready then
    emu.exit()
end
