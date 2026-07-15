MOV #10, R0
MOV #10, R1
CMP R1, R1  
JZ target
MOV #99, R2     
target:
MOV #55, R3   
HALT
