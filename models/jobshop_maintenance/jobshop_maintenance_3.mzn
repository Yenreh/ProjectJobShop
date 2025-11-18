% Job Shop con ventanas de mantenimiento en máquinas
% Opción 3: Input Order con indomain_random

int: jobs;
set of int: JOB = 1..jobs;
int: tasks;
set of int: TASK = 1..tasks;
array [JOB,TASK] of int: d;
int: total = sum(i in JOB, j in TASK)(d[i,j]);

% Ventanas de mantenimiento
int: Nbreaks;
set of int: BRK = 1..Nbreaks;
array [BRK] of int: brk_m;
array [BRK] of int: brk_a;
array [BRK] of int: brk_b;

constraint forall(b in BRK)(
    brk_a[b] < brk_b[b] /\
    brk_m[b] >= min(TASK) /\ brk_m[b] <= max(TASK)
);

int: total_break =
    (if Nbreaks > 0 then sum(b in BRK)(brk_b[b] - brk_a[b]) else 0 endif);
int: horizon = total + total_break;
int: digs = ceil(log(10.0, max(1,horizon)));

% Variables
array [JOB,TASK] of var 0..horizon: s;
var 0..horizon: end;

% Predicado
predicate no_overlap(var int:s1, int:d1, var int:s2, int:d2) =
    s1 + d1 <= s2 \/ s2 + d2 <= s1;

% Restricciones
constraint
    forall(i in JOB)(
        forall(j in 1..tasks-1)( s[i,j] + d[i,j] <= s[i,j+1] ) /\
        s[i,tasks] + d[i,tasks] <= end
    );

constraint
    forall(j in TASK)(
        forall(i,k in JOB where i < k)(
            no_overlap(s[i,j], d[i,j], s[k,j], d[k,j])
        )
    );

constraint
    forall(b in BRK)(
        let {
            int: m = brk_m[b],
            int: a = brk_a[b],
            int: len = brk_b[b] - brk_a[b]
        } in
        forall(i in JOB)(
            no_overlap(s[i,m], d[i,m], a, len)
        )
    );

% Búsqueda: Input Order con indomain_random
solve
  :: int_search(array1d(s), input_order, indomain_random)
  minimize end;

output
  ["end = \(end)\n"] ++
  [ show_int(digs,s[i,j]) ++ " " ++
    if j == tasks then "\n" else "" endif
  | i in JOB, j in TASK ];
