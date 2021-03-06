import math
import numpy as np
import os

distrib = np.loadtxt(f"{os.path.dirname(os.path.realpath(__file__))}/E2.fallos.txt")
mu = distrib.mean()
sigmaCuad = distrib.var()
sigma = distrib.std()

x1 = (0, 0.55)
x2 = (1000, 1.65)
slope = (x2[1] - x1[1]) / (x2[0] - x1[0])
b = x1[1] # It is x[1] since l(x) = ax + b and l(0)=x[1]

# l(x) = ax + b
def ratio(x):
    return slope * x + b


class Machine():
    def __init__(self):
        self.break_time = self.get_break_time(0)

    def get_break_time(self, now):
        return math.trunc(np.random.normal(mu, sigma)*100 + now)

    def set_new_break_time(self, now):
        self.break_time = self.get_break_time(now)


class Repairman():
    def __init__(self):
        self.end_repair_time = self.get_repair_time(0)
        self.repairing_machine = None

    def get_repair_time(self, now):
        lambda_param = ratio(now/100)
        maq_frac_hora = np.random.exponential(1/lambda_param)*100
        return math.trunc(maq_frac_hora + now)

    def set_repair_time(self, now, machine):
        self.end_repair_time = self.get_repair_time(now)
        self.repairing_machine = machine


def simulate(
    n_working_machines=10,
    n_repairmen=3,
    n_waiting_machines=4,
    end=100000,
    verbose=False,
):
    working = [Machine() for i in range(n_working_machines)]
    waiting = [Machine() for i in range(n_waiting_machines)]
    repairmen = [Repairman() for i in range(n_repairmen)]
    repairmen_working = []
    waiting_repair = []
    repairing = []
    working_time = 0
    not_working_time = 0
    all_repairmen_working_time = 0
    events_stack = sorted([mach.break_time for mach in working])

    working_time+=events_stack[0] # time untill the first event as working time
    
    while events_stack[0] < end:
        events_stack=sorted(list(set(events_stack))) # Remove duplicates and sort just in case
        time = events_stack.pop(0)
        
        if verbose:
            print(f"________{time}________")
            print(events_stack)
        for i, machine in enumerate(working):
            if machine and verbose:
                print(f"Machine break time: {machine.break_time}")
            if machine and machine.break_time == time:
                waiting_repair.append(machine)
                try:
                    new_mach = waiting.pop(0)  # First machine in the queue
                    new_mach.set_new_break_time(time)
                    events_stack.append(new_mach.break_time)
                    events_stack=sorted(list(set(events_stack))) # Remove duplicates and sort just in case
                    working[i] = new_mach
                except IndexError:
                    if verbose:
                        print("Se ha roto y no hay + máquinas")
                    working[i] = None
                if verbose and working[i]:
                    print(f"Se rompe en t={time}, la cola es ahora: {len(waiting)}, hay: {sum(x is None for x in working)} Nones, La nueva se romperá en t = {new_mach.break_time} ")
                    print("___________________________________________________________________________________________")

        removers = []
        for i, repairman in enumerate(repairmen_working):
            if repairman.end_repair_time == time:
                repaired_machine = repairing.pop(repairing.index(repairman.repairing_machine))
                waiting.append(repaired_machine)
                repairmen.append(repairman)
                removers.append(i)
        repairmen_working = [
            rep for i, rep in enumerate(repairmen_working) if i not in removers
        ]            
                    
        removers = []
        for i, repairman in enumerate(repairmen):
            if waiting_repair:
                machine = waiting_repair.pop(0)
                repairman.set_repair_time(time, machine)
                events_stack.append(repairman.end_repair_time)
                events_stack=sorted(list(set(events_stack))) # Remove duplicates and sort just in case
                repairmen_working.append(repairman)
                repairing.append(machine)
                removers.append(i)
                if verbose:
                    print(f"Hay waiting en t = {time}, la máquina estará en t = {repairman.end_repair_time}")
                    print("-------------------------------------------------------------------------------------------")
        repairmen = [rep for i, rep in enumerate(repairmen) if i not in removers]

        if None in working and waiting:
            if verbose:
                print(f"Vamos a rellenar. Hay {sum(x is None for x in working)} Nones y waiting es {len(waiting)}")
            for _ in range(sum(x is None for x in working)):
                try:
                    new_machine = waiting.pop(0)
                    new_machine.set_new_break_time(time)
                    events_stack.append(new_machine.break_time)
                    events_stack=sorted(list(set(events_stack))) # Remove duplicates and sort just in case
                    working.append(new_machine)
                    working.remove(None)
                except IndexError:
                    if verbose:
                        print(f"No hay más máquinas para añadir, se quedan {sum(x is None for x in working)} None")
                    break
            if verbose:
                print("...........................................................................................")
        events_stack=sorted(list(set(events_stack))) # Remove duplicates and sort just in case
        next_event=events_stack[0]
        if None not in working:
            working_time += (min(end, next_event) - time)
        if not repairmen:
            all_repairmen_working_time += (min(end, next_event) - time)
        if verbose:
            print("Working time:", working_time)
    if verbose:
        print(not_working_time, working_time, not_working_time + working_time)
    return working_time / end, all_repairmen_working_time / end


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="SSD simulation.")
    parser.add_argument("--n_working_machines", default=10, type=int, help="Number of working machines needed to have the factory working",)
    parser.add_argument("--n_repairmen", default=3, type=int, help="Number of machines that can be repaired at a time.",)
    parser.add_argument("--n_waiting_machines", default=4, type=int, help="Number of machines in the queue if a working machine fails.",)
    parser.add_argument("--end", default=end, type=int, help="Time of the simulation in hours.",)
    parser.add_argument("-v", "--verbose", default=False, type=bool, help="Wether to print ongoing events or not."),

    args = parser.parse_args()
    result = simulate(
        n_working_machines=args.n_working_machines,
        n_repairmen=args.n_repairmen,
        n_waiting_machines=args.n_waiting_machines,
        end=args.end,
        verbose=args.verbose,
    )
    print(result)
