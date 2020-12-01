import numpy as np
import sys
import os
from data_generator import simulation_generator


class DemandGenerator:
    def __init__(self, data, ss_dict, sku, cd_list):
        self.data = data
        self.ss_dict = ss_dict
        self.sku = sku
        self.cd_list = cd_list

        self.buildGenerators()

    def buildGenerators(self):
        self.demand_generators = {}
        for cd in self.cd_list:
            self.demand_generators[cd] = \
                simulation_generator(self.data, self.ss_dict, self.sku, cd)

    def generateUniformDemand(self):
        return np.random.randint(10, 20)

    def generateDemand(self, cd):
        demand, s, S = next(self.demand_generators[cd])
        return demand


class DC:
    def __init__(self, name, hub, stock, policy, lead_time):
        self.name = name
        self.hub = hub

        self.stock = stock
        self.policy = policy
        self.lead_time = lead_time

        self.accumulated_demand = 0
        self.broken_demand = 0

        self.units_on_the_way = 0
        self.days_until_restock = -1

    def receiveDemand(self, demand, hub_n_spoke):
        print(f'Recibiendo {demand} unidades de demanda en {self.name}')

        self.accumulated_demand += demand

        lost = 0
        surpassed_demand = max(0, demand - self.stock)
        if surpassed_demand and self.hub is not None:
            if self.hub.stock >= surpassed_demand:
                print(f'Demanda en CD {self.name} superada.', end=' ')

                if hub_n_spoke:
                    print(f'Hub {self.hub.name} supliendo la demanda por '
                          f'{surpassed_demand} de CD {self.name}.')
                    self.hub.stock -= surpassed_demand
                    print(f'Stock en {self.hub.name}: {self.stock}.')
                else:
                    print()

            else:
                lost = surpassed_demand
        else:
            lost = surpassed_demand

        if lost:
            print(f'Demanda superada por {lost} unidades en {self.name}.')
            self.broken_demand += lost

        self.stock = max(0, self.stock - demand)
        print(f'Stock en {self.name}: {self.stock}.')

        reorder, quantity = self.criterion()
        if reorder and not self.units_on_the_way:
            print(f'Generando orden por {quantity} unidades en '
                  f'{self.name}.')
            self.generateRestockOrder(quantity)

        return lost

    def criterion(self):
        s, S = self.policy
        if self.stock < s:
            quantity = S - self.stock
            return True, quantity
        return False, 0

    def generateRestockOrder(self, quantity):
        self.units_on_the_way = quantity
        self.days_until_restock = self.lead_time

    def restock(self):
        if self.days_until_restock == 0:
            print(f'Rellenando inventario con {self.units_on_the_way} unidades '
                  f'en {self.name}.')
            self.stock += self.units_on_the_way
            print(f'Stock en {self.name}: {self.stock}')
            self.units_on_the_way = 0
            self.days_until_restock -= 1
            return True

        if self.days_until_restock != -1:
            print(f'{self.days_until_restock} días hasta que lleguen '
                  f'{self.units_on_the_way} unidades '
                  f'de inventario en {self.name}.')
            self.days_until_restock -= 1
            return True

        return False


class Hub(DC):
    def __init__(self, name, hub, stock, policy, lead_time):
        super().__init__(name, hub, stock, policy, lead_time)
        self.assigned_dcs = []

    def assignDC(self, dc):
        self.assigned_dcs.append(dc)


class System:
    def __init__(self, hub):
        self.hub = hub

    def resetStats(self):
        self.accumulated_demand = 0
        self.lost_demand = 0

    def showStats(self):
        print()
        print(f'Demanda recibida: {self.accumulated_demand}')
        print(f'Demanda perdida: {self.lost_demand}')

    def simulate(self, demand_generator, T, hub_n_spoke=False, show_stats=True):
        self.resetStats()

        t = 0
        while t < T:
            t += 1

            print(f'\n[Día {t}]\n')

            print(f'Stock en {self.hub.name}: {self.hub.stock}')
            for dc in self.hub.assigned_dcs:
                print(f'Stock en {dc.name}: {dc.stock}')
            print()

            # Revisamos si corresponde que llegue algún pedido al hub
            skip_line = self.hub.restock()

            # Recorremos los centros de distribución
            for dc in self.hub.assigned_dcs:
                if not skip_line:

                # Revisamos si corresponde que llegue algún pedido al cd
                    skip_line = dc.restock()
                else:
                    dc.restock()

            if skip_line:
                print()

            # Recibimos la demanda en el hub
            demand = demand_generator.generateDemand(self.hub.name)
            self.lost_demand += self.hub.receiveDemand(demand, hub_n_spoke)

            self.accumulated_demand += demand

            # Recorremos los centros de distribución
            for dc in self.hub.assigned_dcs:
                # Recibimos las demandas en los centros de distribución
                demand = demand_generator.generateDemand(dc.name)
                self.lost_demand += dc.receiveDemand(demand, hub_n_spoke)

                self.accumulated_demand += demand

        if show_stats:
            self.showStats()

        return self.accumulated_demand, self.lost_demand
