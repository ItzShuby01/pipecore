MOV #10, R0
MOV #20, R1
CMP R0, R1      ; Computes 10 - 20 = -10 (Sets N = 1, V = 0 -> N != V)
JLT target
MOV #99, R2  
target:
MOV #55, R3    
HALT
