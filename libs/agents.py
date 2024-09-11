import json
import os
import copy
import random
from libs import wals_utils as wu
import math
import pickle

# GLOBAL VARIABLES
with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
    domain_elements_pk_by_parameter_pk = json.load(f)
with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
    parameter_pk_by_name_filtered = json.load(f)

class LanguageParameter:
    #TODO check if the param in that language is known and lock it if it is
    def __init__(self, parameter_name, priors_language_pk_list = [], verbose=True):
        self.verbose = verbose
        self.name = parameter_name
        self.priors_language_pk_list = priors_language_pk_list
        # a locked boolean is used for parameters with known value.
        self.locked = False
        if self.verbose:
            print("Language Parameter {} initialization, verbose is on.".format(self.name))
        # param pk
        if parameter_name in wu.parameter_pk_by_name:
            self.parameter_pk = str(wu.parameter_pk_by_name[parameter_name])
            if verbose:
                print("LanguageParameter {}: pk = {}".format(self.name, self.parameter_pk))
        else:
            self.parameter_pk = "none"
        # values
        if self.parameter_pk in domain_elements_pk_by_parameter_pk:
            self.values = domain_elements_pk_by_parameter_pk[self.parameter_pk]
        else:
            self.values = []
        # beliefs
        self.beliefs = {}
        self.beliefs_history = []
        self.observations_inbox = []
        self.message_inbox = []

    def initialize_beliefs_with_wals(self):
        depks = domain_elements_pk_by_parameter_pk[self.parameter_pk]
        # initialize with statistical priors
        self.beliefs = wu.compute_param_distribution(self.parameter_pk,
                                                            self.priors_language_pk_list)
        self.beliefs_history.append(copy.deepcopy(self.beliefs))
        if self.verbose:
            print("LanguageParameter {}: Beliefs initialized with WALS: {}".format(self.name, self.beliefs))
            print("beliefs_history of LanguageParameter {} updated by initialize_beliefs_with_wals, length {}".format(self.name, len(self.beliefs_history)))
            print(self.beliefs_history)


    def inject_peak_belief(self, depk, probability, locked=False):
        if self.verbose:
            print("LanguageParameter {}: Injecting peak belief {} in value {}.".format(self.name, probability, depk))
        p_yes = probability
        p_not = (1 - probability)/(len(self.values) - 1)
        beliefs = {}
        for value in self.values:
            if value == depk:
                beliefs[str(value)] = p_yes
            else:
                beliefs[str(value)] = p_not
        self.beliefs = beliefs
        if locked:
            self.locked = True
        print(self.beliefs)
        self.beliefs_history.append(copy.deepcopy(self.beliefs))
        if self.verbose:
            print("LanguageParameter {}: beliefs_history updated by inject_peak_belief, length {}.".format(self.name, len(self.beliefs_history)))
            print(self.beliefs_history)


    def update_beliefs_from_observations(self, influence_distribution = "uniform", observation_influence=0.6, autolock_threshold=0.99, verbose=True):
        """this function takes in the observation inbox a dict of observation counts of the values of the said parameter
        and uses it to update the corresponding uncertain variable.
        observations is of the form {value1: count1, value2: count2...}"""
        #TODO Implement non uniform influence distribution
        # check if the observations given include all the values
        if verbose:
            print("LanguageParameter {}: Updating current beliefs with {} observations".format(self.name, len(self.observations_inbox)))
        if self.locked:
            print("Language Parameter {}: value locked. Observations not taken into account.".format(self.name))
        else:
            for observations in self.observations_inbox:
                values_check = True
                for de_pk in self.beliefs.keys():
                    if de_pk not in observations.keys():
                        values_check = False
                if values_check:
                    priors = self.beliefs
                    if verbose:
                        print("LanguageParameter {}: Priors: {}".format(self.name, priors))
                    n_values = len(observations.keys())
                    if n_values > 1:
                        p_yes = observation_influence
                        p_not = (1 - p_yes)/(n_values - 1)
                    else:
                        print("there's just one value... can't update beliefs.")
                        return False
                    total_number_of_observations = 0
                    for de_pk in observations.keys():
                        total_number_of_observations += observations[de_pk]

                    # multinomial factor used to account for hidden parameters
                    multinomial_factor_numerator = math.factorial(total_number_of_observations)
                    multinomial_factor_denominator = 1
                    for obs in observations.keys():
                        multinomial_factor_denominator = multinomial_factor_denominator * math.factorial(observations[obs])
                    multinomial_factor = multinomial_factor_numerator / multinomial_factor_denominator
                    # likelihoods, probabilities of observing these observations given that the true value is X
                    # P(Observations | X = xi)
                    likelihoods = {}
                    for de_pk in observations.keys():
                        # assuming this de_pk is the true value, compute the probability of making these observations
                        likelihoods[de_pk] = multinomial_factor
                        for observation_key in observations.keys():
                            if observation_key == de_pk:
                                likelihoods[de_pk] = likelihoods[de_pk] * math.pow(p_yes, observations[observation_key])
                            else:
                                likelihoods[de_pk] = likelihoods[de_pk] * math.pow(p_not, observations[observation_key])
                    if verbose:
                        print("LanguageParameter {}: Likelihoods: {}".format(self.name, likelihoods))
                    # update of current beliefs (priors)
                    # normalization factor
                    normalization_factor = 0
                    for de_pk in observations:
                        normalization_factor += likelihoods[de_pk]*priors[de_pk]
                    # updating beliefs
                    posteriors = {}
                    for de_pk in observations:
                        posteriors[de_pk] = likelihoods[de_pk] * priors[de_pk] / normalization_factor
                    self.beliefs = posteriors
                    self.beliefs_history.append(copy.deepcopy(self.beliefs))
                    if verbose:
                        print("LanguageParameter {}: posteriors: {}".format(self.name, posteriors))
                        print("LanguageParameter {}: beliefs_history updated by observations, length {}.".format(self.name, len(self.beliefs_history)))
                        print(self.beliefs_history)
                    # AUTOLOCK
                    for belief in self.beliefs:
                        if self.beliefs[belief] > autolock_threshold:
                            self.locked = True
                            if self.verbose:
                                print("LanguageParameter {}: lock is on. Belief {} at {}, above threshold {}.".format(self.name,
                                                                                                               belief,
                                                                                                               self.beliefs[
                                                                                                                   belief],
                                                                                                              autolock_threshold
                                                                                                               ))
            self.observations_inbox = []

# ************************************************************************

class GeneralAgent:
    """ A general agent looks at a set of parameters independently of constructions.
    by default, all parameters a general agent observe are considered as nodes of a non-directed,
    fully connected graph."""
    def __init__(self, name, parameter_names=[], connection_map={}, language_stat_filter={}, verbose=True):
        self.verbose = verbose
        if self.verbose:
            print("General Agent {} initialization, verbose is on.".format(name))
        self.name = name
        self.language_stat_filters = language_stat_filter
        self.language_pks_used_for_statistics = []
        # the different parameters the general agent is focusing on
        self.parameter_names = parameter_names
        self.language_parameters = {}
        self.graph = {}

        # populate language_pks_used_for_statistics
        self.initialize_list_of_language_pks_used_for_statistics()

        # create and initialize instances of LanguageParameters objects
        for parameter_name in self.parameter_names:
            if parameter_name in wu.parameter_pk_by_name:
                new_language_parameter = LanguageParameter(parameter_name, self.language_pks_used_for_statistics)
                self.language_parameters[parameter_name] = new_language_parameter
                new_language_parameter.initialize_beliefs_with_wals()
            else:
                print("General Agent {}: parameter name {} not in parameter_pk_by_name, discarding.".format(self.name, parameter_name))
        if verbose:
            print("General Agent {}: {} instances of LanguageParameter objects initialized.".format(self.name, len(self.language_parameters)))

        # initialize graph
        #creating a unique graph name
        self.graph_name = "ga_graph_" + str(len(self.language_pks_used_for_statistics)) + "_"
        for p in self.language_parameters:
            self.graph_name += p[-3:] + "_"
        self.initialize_graph()

    def reset_language_parameters_beliefs_with_wals(self):
        for lp_name, lp in self.language_parameters.items():
            lp.beliefs_history = []
            lp.initialize_beliefs_with_wals()

    def initialize_graph(self, alternate_graph={}):
        """ creates the graph between parameters supporting interactions.
        By default, the graph is fully connected. The alternate_graph param can pass another graph to use.
        The graph is represented by a dict of nodes which values are a dict of other nodes it is connected
        to, which value is the potential function."""
        if self.verbose:
            print("Agent {}: initializing graph.")
        if alternate_graph != {}:
            self.graph = alternate_graph
        elif self.graph_name + ".pkl" in os.listdir("./data/general_agents_graphs/"):
            if self.verbose:
                print("Existing graph {} pickled, loading it.".format(self.graph_name + ".pkl"))
            with open("./data/general_agents_graphs/" + self.graph_name + ".pkl", "rb") as f:
                self.graph = pickle.load(f)
        else:
            if self.verbose:
                print("No graph {} found, creating it".format(self.graph_name + ".pkl"))
            for language_parameter_name in self.language_parameters.keys():
                self.graph[language_parameter_name] = {}
                for lpn in self.language_parameters.keys():
                    if lpn != language_parameter_name:
                        potential_function = wu.compute_potential_function_from_general_data(
                            self.language_parameters[language_parameter_name].parameter_pk,
                            self.language_parameters[lpn].parameter_pk
                        )
                        self.graph[language_parameter_name][lpn] = potential_function
            # with open("./data/general_agents_graphs/" + self.graph_name + ".pkl", "wb") as f:
            #     pickle.dump(self.graph, f)
            #     if self.verbose:
            #         print("Graph pickled and saved as {}.".format("./data/general_agents_graphs/" + self.graph_name + ".pkl"))
        print("Agent {}: Graph initialized.".format(self.name))

    def initialize_list_of_language_pks_used_for_statistics(self):
        if self.verbose:
            print("Agent {}: build_language_pks_used_for_statistics...".format(self.name))
        if self.language_stat_filters != {}:
            if "family" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["family"]:
                    self.language_pks_used_for_statistics += wu.get_language_pks_by_family(f)
            if "subfamily" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["subfamily"]:
                    self.language_pks_used_for_statistics +=  wu.get_language_pks_by_subfamily(f)
            if "genus" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["genus"]:
                    self.language_pks_used_for_statistics += wu.get_language_pks_by_genus(f)
            if "macroarea" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["macroarea"]:
                    self.language_pks_used_for_statistics += wu.get_language_pks_by_macroarea(f)
            self.language_pks_used_for_statistics = list(set(self.language_pks_used_for_statistics))
        else:
            self.language_pks_used_for_statistics = list(wu.language_by_pk.keys())
        if self.verbose:
            print("Agent {}: {} languages used for statistics.".format(self.name, len(self.language_pks_used_for_statistics)))

    def run_belief_update_cycle(self):
        path = self.create_random_propagation_path()
        # update each parameter's beliefs from observations and neighbors messages
        for p_name in path:
            self.language_parameters[p_name].update_beliefs_from_observations()
            self.update_beliefs_from_messages_received(p_name)
        # run messaging round
        self.run_message_round()


    def run_message_round(self):
        messages = {}
        path = self.create_random_propagation_path()
        for sender_name in path:
            for recipient_name in path:
                if recipient_name != sender_name:
                    message = self.generate_message(sender_name, recipient_name)
                    self.language_parameters[recipient_name].message_inbox.append(message)
                    messages[sender_name + "->" + recipient_name] = message
                    if self.verbose:
                        print("Message {}->{}: {}".format(sender_name, recipient_name, message))

    def create_random_propagation_path(self):
        """ List of parameters indicating the order in which the belief propagation is executed."""
        path = self.parameter_names.copy()
        random.shuffle(path)
        if self.verbose:
            print("General Agent {}: Random belief propagation path is {}".format(self.name, path))
        return path

    def add_observations(self, parameter_name, observations):
        """ add observations to a LanguageParameter observation inbox."""
        if self.verbose:
            print("Agent {}: adding observation {} to LanguageParameter {}.".format(self.name, observations, parameter_name))
        if parameter_name in self.language_parameters.keys():
            self.language_parameters[parameter_name].observations_inbox.append(observations)

    def update_beliefs_from_messages_received(self, parameter_name):
        # messages are dicts where keys are the recipient's values and values the neighbor's belief about it.
        if self.language_parameters[parameter_name].locked:
            if self.verbose:
                print("General Agent {}: Parameter {} is locked: not updating its beliefs from messages.".format(self.name, parameter_name))
        else:
            if self.verbose:
                print("General Agent {}: Updating beliefs of parameter {} based on {} messages from neighbors. Old beliefs = {}".format(self.name, parameter_name, len(self.language_parameters[parameter_name].message_inbox), self.language_parameters[parameter_name].beliefs))
            sum = 0
            for value in self.language_parameters[parameter_name].beliefs.keys():
                for message in self.language_parameters[parameter_name].message_inbox:
                    if value in message.keys():
                        self.language_parameters[parameter_name].beliefs[value] *= message[value]
                sum += self.language_parameters[parameter_name].beliefs[value]
            for value in self.language_parameters[parameter_name].beliefs.keys():
                self.language_parameters[parameter_name].beliefs[value] = self.language_parameters[parameter_name].beliefs[value] / sum
            self.language_parameters[parameter_name].beliefs_history.append(copy.deepcopy(self.language_parameters[parameter_name].beliefs))
            if self.verbose:
                print("General Agent {}: beliefs_history of LanguageParameter {} updated by update_beliefs_from_messages_received, length {}.".format(self.name, parameter_name, len(self.language_parameters[parameter_name].beliefs_history)))
                print(self.language_parameters[parameter_name].beliefs_history)
            self.language_parameters[parameter_name].message_inbox = []
            if self.verbose:
                print("Agent {}: Beliefs of parameter {} updated by neighbors messages. New beliefs: {}".format(self.name, parameter_name, self.language_parameters[parameter_name].beliefs))

    def generate_message(self, p1_name, p2_name):
        """ message from parameter p1 to parameter p2.
        The message is a dict of dimension the number of values of the receiving parameter."""
        p1 = self.language_parameters[p1_name]
        p2 = self.language_parameters[p2_name]
        message = {}
        potential = self.graph[p1.name][p2.name]
        sum = 0
        for v2 in p2.values:
            message[str(v2)] = 0
            for v1 in p1.values:
                try:
                    message[str(v2)] += potential.at[v1, v2] * p1.beliefs[str(v1)]
                except KeyError:
                    print("Issue generating part of a message from {} to {}, values v1={}, v2={}. Term ignored".format(p1_name, p2_name, v1, v2))
            sum += message[str(v2)]
        for v2 in p2.values:
            if sum != 0:
                message[str(v2)] = message[str(v2)] / sum
        return message







