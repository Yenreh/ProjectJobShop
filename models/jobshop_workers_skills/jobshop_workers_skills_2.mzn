enum JOB;
enum TASK;
TASK: last = max(TASK);
array [JOB,TASK] of int: d;
int: total = sum(i in JOB, j in TASK)(d[i,j]);
int: digs = ceil(log(10.0,int2float(total)));
array [JOB,TASK] of var 0..total: s;
var 0..total: end;

% Parámetros para operarios
int: W;
set of int: WORKER = 1..W;
array[TASK] of set of WORKER: skills;

% variable de asignación: a cada operación (job,task) se le asigna un operario
array[JOB,TASK] of var WORKER: w_assign;

% variables de asignación por operario
array[WORKER, JOB, TASK] of var bool: assigned;
constraint
  forall(w in WORKER, i in JOB, j in TASK) (
    assigned[w,i,j] = (w_assign[i,j] == w)
  );

% Secuencia interna de tareas por job
constraint
    forall(i in JOB) (
        forall(j in TASK where j < last) 
            (s[i,j] + d[i,j] <= s[i,enum_next(TASK,j)]) /\
        s[i,last] + d[i,last] <= end
    );

% Restricción de no solapamiento por máquina
constraint
    forall(j in TASK) (
        forall(i,k in JOB where i < k) (
            s[i,j] + d[i,j] <= s[k,j] \/
            s[k,j] + d[k,j] <= s[i,j]
        )
    );

% Restricción: cada tarea debe ser asignable sólo a operarios con la skill
constraint
    forall(i in JOB, j in TASK) (
        w_assign[i,j] in skills[j]
    );

% Restricción: un mismo operario no puede ejecutar dos tareas solapadas
constraint
  forall(w in WORKER,
         i1 in JOB, j1 in TASK,
         i2 in JOB, j2 in TASK where (i1 < i2 \/ (i1 == i2 /\ j1 < j2))) (
    assigned[w,i1,j1] + assigned[w,i2,j2] <= 1 \/
    s[i1,j1] + d[i1,j1] <= s[i2,j2] \/
    s[i2,j2] + d[i2,j2] <= s[i1,j1]
  );

% Cálculo de cargas por operario para balanceo
array[WORKER] of var 0..total: load =
  [ sum(i in JOB, j in TASK)( d[i,j] * bool2int(assigned[w,i,j]) ) | w in WORKER ];

var 0..total: maxLoad;
var 0..total: minLoad;
constraint maxLoad = max(load);
constraint minLoad = min(load);

% Objetivo: priorizar makespan y luego balancear la carga
int: BIG = total + 1;
solve
:: seq_search([
     int_search([s[i,j] | i in JOB, j in TASK], dom_w_deg, indomain_min),
     int_search([w_assign[i,j] | i in JOB, j in TASK], first_fail, indomain_min)
   ])
minimize BIG * end + maxLoad;

% Salida
output [
  "end = \(end)\n",
  "Carga por operario (load):\n"
] ++
[ "w" ++ show(w) ++ ": " ++ show(load[w]) ++ if w == max(WORKER) then "\n" else "\n" endif | w in WORKER ]
++ [
  "Asignaciones (job task -> worker):\n"
] ++
[ show_int(digs,s[i,j]) ++ " " ++
  if j == last then " -> w=" ++ show(w_assign[i,j]) ++ "\n" else " -> w=" ++ show(w_assign[i,j]) ++ " | " endif
  | i in JOB, j in TASK ];
