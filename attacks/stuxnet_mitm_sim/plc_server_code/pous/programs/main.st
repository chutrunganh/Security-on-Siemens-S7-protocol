PROGRAM main
VAR
	iSimSpeed : int AT %IW0;
	iSetpoint : int AT %IW1 := 1200;
	iCounter : int := 0;
	bCentrifugeStatus : bool AT %QX0.0;
END_VAR

iCounter := iCounter + 1;
IF iCounter > 628 THEN
    iCounter := 0;
END_IF;

IF iCounter <= 314 THEN
    iSimSpeed := iSetpoint + (iCounter * 200 / 314) - 300;  
ELSE
    iSimSpeed := iSetpoint + 100 - ((iCounter - 314) * 300 / 314);
END_IF;

IF iSimSpeed > 1500  THEN
    bCentrifugeStatus := TRUE;
ELSE
    bCentrifugeStatus := FALSE;
END_IF;

END_PROGRAM