; Cooperative producer for ROM-resident PPU update streams

.segment "PRG_STATIC_PPU_UPDATE_QUEUE"

QueueStaticPpuUpdateStream:
    LDX PpuUpdateStreamPointer + 1
    BEQ PublishSelectedStaticPpuUpdateStream
    PHA
    JSR SwitchThreads
    PLA
    BCS QueueStaticPpuUpdateStream

PublishSelectedStaticPpuUpdateStream:
    TAX
    LDA StaticPpuUpdatePointerLowTable,X
    STA PpuUpdateStreamPointer
    LDA StaticPpuUpdatePointerHighTable,X
    STA PpuUpdateStreamPointer + 1
    RTS
