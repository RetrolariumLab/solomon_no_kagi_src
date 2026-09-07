; Resolve a non-Dana object index to its runtime record

.segment "PRG_LOAD_OBJECT_POINTER"

LoadObjectPointer:
    LDA NonDanaObjectPointerLowTable,X
    STA TempPointer00
    LDA NonDanaObjectPointerHighTable,X
    STA TempPointer00 + 1
    RTS
