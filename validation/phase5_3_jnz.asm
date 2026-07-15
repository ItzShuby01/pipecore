MOV #10, R0
MOV #20, R1
CMP R0, R1      ; Sets Z = 0
JNZ target
MOV #99, R2     ; Must be skipped
target:
MOV #55, R3    ; Must execute
HALT
