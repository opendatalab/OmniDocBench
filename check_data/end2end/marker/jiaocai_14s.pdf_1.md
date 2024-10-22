
## Chapter 14 Transactions

conflict serializable schedules. The general form of view serializability is very expensive to test, and only a very restricted form of it is used for concurrency control.

14.6
Answer:  There is a serializable schedule corresponding to the precedence graph below, since the graph is acyclic. A possible schedule is obtained by doing a topological sort, that is, T1, T2, T3, T4, T5.

14.7 Answer: A cascadeless schedule is one where, for each pair of transactions Ti and T; such that T; reads data items previously written by T;, the commit operation of Ti appears before the read operation of Tj. Cascadeless schedules are desirable because the failure of a transaction does not lead to the aborting of any other transaction. Of course this comes at the cost of less concurrency. If failures occur rarely, so that we can pay the price of cascading aborts for the increased concurrency, noncascadeless schedules might be desirable.

## 14.8 Answer:

a. 

A schedule showing the Lost Update Anomaly:
T1 T2

| read(A)   | read(A)   |
|-----------|-----------|
| write(A)  |           |

write(A)
In the above schedule, the value written by the transaction T2 is lost because of the write of the transaction T1.

b.

| T1        | T2        |
|-----------|-----------|
| lock-S(A) |           |
| read(A)   |           |
| unlock(A) | lock-X(A) |
| read(A)   |           |
| write(A)  |           |
| unlock(A) |           |
| commit    |           |
| lock-X(A) |           |

Lost Update Anomaly in Read Committed Isolation Level write(A) unlock(A) commit The locking in the above schedule ensures the Read Committed isolation level. The value written by transaction T2 is lost due to T1's write.

C.

![0_image_0.png](0_image_0.png)

Lost Update Anomaly is not possible in Repeatable Read isolation level. In repeatable read isolation level, a transaction 71 reading a

## N
