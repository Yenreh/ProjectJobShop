include "globals.mzn";

/************ Parámetros ************/
int: jobs;  int: tasks;  int: k;
set of int: JOB = 1..jobs;
set of int: TASK = 1..tasks;
set of int: OP   = 1..k;
array[JOB, TASK] of int: d;

int: total = sum(i in JOB, j in TASK)(d[i,j]);
int: digs  = ceil(log(10.0, total));

/************ Variables ************/
array[JOB, TASK] of var 0..total: s;
array[JOB, TASK] of var OP: o;
var 0..total: end;

array[OP] of var bool: used;
array[OP] of var 0..total: carga;

/************ Job shop base ************/
constraint forall(i in JOB, j in 1..tasks-1) (s[i,j] + d[i,j] <= s[i,j+1]);
constraint forall(j in TASK) (
  disjunctive([s[i,j] | i in JOB], [d[i,j] | i in JOB])
);
constraint forall(i in JOB) (s[i,tasks] + d[i,tasks] <= end);

/************ Operarios: no solape si comparten operario ************/
constraint forall(i1 in JOB, j1 in TASK, i2 in JOB, j2 in TASK where (i1,j1) < (i2,j2)) (
  (o[i1,j1] = o[i2,j2]) ->
  (s[i1,j1] + d[i1,j1] <= s[i2,j2] \/ s[i2,j2] + d[i2,j2] <= s[i1,j1])
);

/* Redundante útil: a lo sumo k tareas simultáneas (poda) */
array[int] of var 0..total: S_all = [ s[i,j] | i in JOB, j in TASK ];
array[int] of int:        D_all = [ d[i,j] | i in JOB, j in TASK ];
array[int] of int:        R_all = [ 1      | i in JOB, j in TASK ];
constraint cumulative(S_all, D_all, R_all, k);

/************ Simetrías de operarios ************/
constraint forall(p in OP) ( used[p] <-> exists(i in JOB, j in TASK)(o[i,j] = p) );
constraint forall(p in 2..k) ( bool2int(used[p]) <= bool2int(used[p-1]) );
constraint o[1,1] = 1;
/* Ordenar cargas no crecientes (rompe simetrías) */
constraint forall(p in 1..k-1)( carga[p] >= carga[p+1] );

/************ Carga y medidas de balanceo ************/
constraint forall(p in OP)(
  carga[p] = sum(i in JOB, j in TASK)( d[i,j] * bool2int(o[i,j] = p) )
);
var 0..total: maxload = max(p in OP)(carga[p]);
var 0..total: minload = min(p in OP)(carga[p]);

/************ Cota opcional para guiar la búsqueda (no cambia factibilidad) ************/
int: ub_end = total;
constraint end <= ub_end;

/************ Salida ************/
output
  [ "end = \(end)\n",
    "carga_por_operario = \(carga)\n",
    "desbalance = \(maxload - minload)\n"
  ]
  ++ [ "Job \(i): " ++
       concat([ show_int(digs, s[i,j]) ++ "(op:" ++ show(o[i,j]) ++ ")"
                ++ (if j < tasks then " " else "" endif)
                | j in TASK ]) ++ "\n"
       | i in JOB ];

/************ OBJETIVO + BÚSQUEDA (elige UNA) ************/
int: W = total + 1;

/* ------------------------------------------------------------------
 * Tiempo con dom_w_deg (más guiado); operarios con first_fail
 * ------------------------------------------------------------------*/
solve
:: seq_search([
     int_search([s[i,j] | i in JOB, j in TASK], dom_w_deg, indomain_min),
     int_search([o[i,j] | i in JOB, j in TASK], first_fail, indomain_min)
   ])
minimize W * end + (maxload - minload);
