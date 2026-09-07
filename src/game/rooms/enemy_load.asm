; Decode the current room's enemy stream into runtime slots

.segment "PRG_ROOM_ENEMY_LOAD"

EnemyAiActiveFlag = $80
EnemySpawnLifetimeLowMask = $E0
EnemySpawnLifetimeHighMask = $1F

LoadRoomEnemies:
    LDX CurrentRoomIndex
    LDA RoomEnemyPointerLowTable,X
    STA RoomEnemyPointer
    LDA RoomEnemyPointerHighTable,X
    STA RoomEnemyPointer + 1
    LDY #$00
    LDA (RoomEnemyPointer),Y
    INY
    TAX
    AND #EnemySpawnLifetimeLowMask
    STA EnemySpawnLifetimeThresholdLo
    TXA
    AND #EnemySpawnLifetimeHighMask
    STA EnemySpawnLifetimeThresholdHi

DecodeNextRoomEnemy:
    LDA (RoomEnemyPointer),Y
    BEQ FinishRoomEnemyLoad
    STA SpawnType
    INY
    STY RoomEnemyStreamOffset
    JSR FindFreeEnemySlotIndex
    STX SpawnSlotIndex
    LDA #EnemyAiActiveFlag
    STA (TempPointer04),Y
    LDY RoomEnemyStreamOffset
    LDA (RoomEnemyPointer),Y
    INC RoomEnemyStreamOffset
    STA MapCellIndex
    JSR ConvertMapIndexToPixelCoordinates
    JSR InitializeEnemy
    JSR ConfigureEnemyType
    LDY RoomEnemyStreamOffset
    BNE DecodeNextRoomEnemy

FinishRoomEnemyLoad:
    RTS
