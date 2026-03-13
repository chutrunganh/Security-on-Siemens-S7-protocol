PROGRAM main
VAR
	StartBtn : bool AT %MX0.0; (* Nút Start - Master ghi vào đây *)
	StopBtn : bool AT %MX0.1; (* Nút Stop - Master ghi vào đây *)
	MotorOut : bool AT %QX0.0; (* Đầu ra Motor - Master đọc từ đây *)
	RunLatch : bool := FALSE; (* Biến chốt nội bộ *)
	AutoOffTimer : TON; (* Bộ định thời tự tắt *)
	AutoOffSetpoint : time := T#10s; (* Thời gian chạy tối đa *)
END_VAR

IF StartBtn THEN
    RunLatch := TRUE;
    {printf("S7 Master requested START\n")}
END_IF;

IF StopBtn THEN
    RunLatch := FALSE;
    {printf("S7 Master requested STOP\n")}
END_IF;

AutoOffTimer(IN := RunLatch, PT := AutoOffSetpoint);
IF AutoOffTimer.Q THEN
    RunLatch := FALSE;
    {printf("Motor AUTO OFF by Timer\n")}
END_IF;

MotorOut := RunLatch;

END_PROGRAM