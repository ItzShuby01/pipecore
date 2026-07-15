MOV #30, R0
MOV #15, R1
CMP R0, R1     ; Computes 30 - 15 = 15 (Sets Z = 0, N = 0, V = 0 -> Z == 0 && N == V)
JGT target
MOV #99, R2    
target:
MOV #55, R3 
HALT
