MOV #100, R1
CALL my_subroutine
MOV #200, R1      
HALT

my_subroutine:
MOV #55, R2 
RET