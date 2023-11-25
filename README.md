# KDS project

## TASK 1 - done
Create application, which is able to transfer a file from 
over the network from one PC to another using UDP. Should 
be capable of transferring hue files by dividing them into 
packets no longer then 1024. 

## TASK 2 
Add <b>HASH</b> check, <b>CRC</b> and <b>ACK</b> messages
(implement stop and wait). Keep in mind timeouts and repeated
sending if no ACK.

Use NetDerper to test your code. 

## TASK 3
Instead of stop and wait implement selective repeat.