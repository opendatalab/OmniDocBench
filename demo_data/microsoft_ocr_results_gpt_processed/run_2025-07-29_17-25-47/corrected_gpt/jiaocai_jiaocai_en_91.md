| UAT | C++ |
| --- | --- |
| UAT | Finance |

In addition, we define that "an employee fits a job" if and only if the employee has all skills that are needed by the job.

Please write relational algebra expressions for the following queries.

1) Find the name of female employees who have at least one skill needed by the "DEV" job.

2) Find the names of employees who fit the "DEV" job.

# 2. SQL Query (20 points, 5 points each)

Consider the relational schemas given in problem 1, please write SQL statements to meet the following requests.

1) Find the employees who have not any skills.

2) Find the jobs that need at least "Java" and "C++" skills.

3) Find the names of employees who have the maximum number of skills among all employees.

4) Find the employees who fit both the "DEV" and "UAT" jobs.

## 3. Embedded SQL (10 points)

Based on the schemas defined in problem 1, the following embedded SQL program accepts the id of an employee as input, and outputs all skills of the employee. Please fill in the blanks of the program.

```c
main() {
    EXEC SQL INCLUDE SQLCA;
    EXEC SQL BEGIN DECLARE SECTION;
    char id[10]; 
    char skill[20];
    EXEC SQL END DECLARE SECTION;

    EXEC SQL CONNECT TO skill_db USER user1 USING password1;

    EXEC SQL DECLARE skill_cursor CURSOR FOR
    SELECT skill FROM employee_skills WHERE employee_id = :id;

    printf("please input employee id: ");
    scanf("%s", id);

    EXEC SQL OPEN skill_cursor;

    for (;;) {
        EXEC SQL FETCH skill_cursor INTO :skill;
        if (sqlca.sqlcode != 0) break;
        printf("%s\n", skill);
    }

    EXEC SQL CLOSE skill_cursor;
    EXEC SQL DISCONNECT;
}
```