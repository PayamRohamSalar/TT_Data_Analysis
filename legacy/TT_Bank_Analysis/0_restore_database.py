RESTORE DATABASE Alzahra
FROM DISK = 'E:\ToseeTaavon_Bank\Alzahra_Backup.bak'
WITH 
    MOVE 'MyDatabase_Primary' TO 'E:\SQLData\Alzahra.mdf', 
    MOVE 'MyDatabase_Log' TO 'E:\SQLData\Alzahra_log.ldf', 
    REPLACE,
    RECOVERY, -- این کلمه تضمین می‌کند دیتابیس در پایان کار آنلاین شود
    STATS = 5;