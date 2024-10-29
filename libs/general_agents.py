import json
import os
import copy
import random
from libs import wals_utils as wu, grambank_utils as gu, grambank_wals_utils as gwu
import math
import pickle

# GLOBAL VARIABLES
try:
    with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
        parameter_pk_by_name_filtered = json.load(f)
except FileNotFoundError:
    with open("../external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
        domain_elements_pk_by_parameter_pk = json.load(f)
    with open("../external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
        parameter_pk_by_name_filtered = json.load(f)

# CLASSES

class LanguageParameter:
    def __init__(self, parameter_name, origin="wals", priors_language_pk_list = [], verbose=False):
        self.verbose = verbose
        self.name = parameter_name
        self.origin = origin
        self.priors_language_pk_list = priors_language_pk_list
        # a locked boolean is used for parameters with known value.
        self.locked = False
        if self.verbose:
            print("Language Parameter {} initialization, verbose is on.".format(self.name))
        # param pk
        if self.origin == "wals":
            if parameter_name in wu.parameter_pk_by_name:
                self.parameter_pk = str(wu.parameter_pk_by_name[parameter_name])
                if verbose:
                    print("WALS LanguageParameter {}: pk = {}".format(self.name, self.parameter_pk))
            else:
                self.parameter_pk = "none"
            # values
            if self.parameter_pk in domain_elements_pk_by_parameter_pk:
                self.values = domain_elements_pk_by_parameter_pk[self.parameter_pk]
                if verbose:
                    print("WALS LanguageParameter {}: values = {}".format(self.name, self.values))
            else:
                print("parameter origin is supposedly wals but {} not found in wals".format(parameter_name))
                self.values = []
        elif self.origin == "grambank":
            if parameter_name in gu.grambank_pid_by_pname:
                self.parameter_pk = str(gu.grambank_pid_by_pname[parameter_name])
                if verbose:
                    print("Grambank LanguageParameter {}: pk = {}".format(self.name, self.parameter_pk))
                # values
                if self.parameter_pk in gu.grambank_param_value_dict:
                    self.values = list(gu.grambank_param_value_dict[self.parameter_pk]["pvalues"].keys())
                    if verbose:
                        print("Grambank LanguageParameter {}: values = {}".format(self.name, self.values))
            else:
                print("parameter origin is supposedly grambank but {} not found in grambank_pid_by_pname".format(parameter_name))
                self.values = []
        else:
            print("Parameter {} origin undefined, values can't be set.".format(parameter_name))
            self.values = []

        # beliefs
        self.beliefs = {}
        self.beliefs_history = []
        self.observations_inbox = []
        self.message_inbox = {}

    def initialize_beliefs_with_grambank(self):
        pvalues = gu.grambank_param_value_dict[self.parameter_pk]["pvalues"].keys()
        self.beliefs = gu.compute_grambank_param_distribution(self.parameter_pk, self.priors_language_pk_list)
        self.beliefs_history.append(copy.deepcopy(self.beliefs))
        if self.verbose:
            print("LanguageParameter {}: Beliefs initialized with Grambank: {}".format(self.name, self.beliefs))

    def initialize_beliefs_with_wals(self):
        depks = domain_elements_pk_by_parameter_pk[self.parameter_pk]
        # initialize with statistical priors
        self.beliefs = wu.compute_wals_param_distribution(self.parameter_pk, self.priors_language_pk_list)
        self.beliefs_history.append(copy.deepcopy(self.beliefs))
        if self.verbose:
            print("LanguageParameter {}: Beliefs initialized with WALS: {}".format(self.name, self.beliefs))

    def inject_peak_belief(self, depk, probability, locked=False):
        if self.verbose:
            print("LanguageParameter {}: Injecting peak belief {} in value {}.".format(self.name, probability, depk))
        p_yes = probability
        p_not = (1 - probability)/(len(self.values) - 1)
        beliefs = {}
        for value in self.values:
            if str(value) == str(depk):
                beliefs[str(value)] = p_yes
            else:
                beliefs[str(value)] = p_not
        self.beliefs = beliefs
        if locked:
            self.locked = True
        #print("updated belief after injection", self.beliefs)
        self.beliefs_history.append(copy.deepcopy(self.beliefs))
        # if self.verbose:
        #     print("LanguageParameter {}: beliefs_history updated by inject_peak_belief, length {}.".format(self.name, len(self.beliefs_history)))
        #     print(self.beliefs_history)


    def update_beliefs_from_observations(self, influence_distribution = "uniform", observation_influence=0.9, autolock_threshold=0.99, verbose=False):
        """this function takes in the observation inbox a dict of observation counts of the values of the said parameter
        and uses it to update the corresponding uncertain variable.
        observations is of the form {value1: count1, value2: count2...}"""
        #TODO Implement non uniform influence distribution
        # check if the observations given include all the values
        if verbose:
            print("LanguageParameter {}: Updating current beliefs with {} observations".format(self.name, len(self.observations_inbox)))
        if verbose and self.locked:
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
    def __init__(self, name, parameter_names=[], language_stat_filter={}, verbose=False):
        self.verbose = verbose
        if self.verbose:
            print("General Agent {} initialization, verbose is {}.".format(name, verbose))
        self.name = name
        self.language_stat_filters = language_stat_filter
        # the different parameters the general agent is focusing on
        self.parameter_names = parameter_names
        self.language_parameters = {}
        self.graph = {}

        # create language_pks_used_for_statistics
        self.wals_languages_used_for_statistics = self.initialize_wals_list_of_language_pks_used_for_statistics()
        self.grambank_languages_used_for_statistics = self.initialize_grambank_list_of_language_pks_used_for_statistics()

        # create and initialize instances of LanguageParameters objects
        for parameter_name in self.parameter_names:
            if parameter_name in wu.parameter_pk_by_name:
                # This is a WALS parameter
                new_language_parameter = LanguageParameter(parameter_name, origin="wals", priors_language_pk_list=self.wals_languages_used_for_statistics, verbose=self.verbose)
                self.language_parameters[parameter_name] = new_language_parameter
                new_language_parameter.initialize_beliefs_with_wals()
            elif parameter_name in gu.grambank_pid_by_pname:
                # This is a Grambank parameter
                new_language_parameter = LanguageParameter(parameter_name, origin="grambank", priors_language_pk_list=self.grambank_languages_used_for_statistics, verbose=self.verbose)
                self.language_parameters[parameter_name] = new_language_parameter
                new_language_parameter.initialize_beliefs_with_grambank()
            else:
                # unknown/custom parameter, ignored.
                # TODO: enable custom parameters
                print("General Agent {}: parameter name {} not in parameter_pk_by_name, discarding.".format(self.name, parameter_name))
        if self.verbose:
            print("General Agent {}: {} instances of LanguageParameter objects initialized.".format(self.name, len(self.language_parameters)))

        # initialize graph
        self.graph_name = "ga_graph_"
        for p in self.language_parameters:
            self.graph_name += p[-3:] + "_"
        self.initialize_graph()

    def get_beliefs(self):
        beliefs = {}
        for lpn in self.language_parameters.keys():
            beliefs[lpn] = self.language_parameters[lpn].beliefs
        return beliefs

    def reset_language_parameters_beliefs_with_wals(self):
        for lp_name, lp in self.language_parameters.items():
            lp.beliefs_history = []
            lp.initialize_beliefs_with_wals()

    def initialize_graph(self, alternate_graph={}):
        """ creates the graph between parameters supporting interactions.
        By default, the graph is fully connected. The alternate_graph param can pass another graph to use.
        The graph is represented by a dict of nodes. Each Pi node's value is a dict of other Pj nodes it is connected
        to, each of these nodes with the value (Pj given Pi) matrix."""
        if self.verbose:
            print("Agent {}: initializing graph.")
        if alternate_graph != {}:
            self.graph = alternate_graph
        else:
            for lpn1 in self.language_parameters.keys():
                self.graph[lpn1] = {}
                for lpn2 in self.language_parameters.keys():
                    # add edge and compute only if both wals or grambank
                    if lpn1 in wu.parameter_pk_by_name.keys() and lpn2 in wu.parameter_pk_by_name.keys() and lpn2 != lpn1:
                        cp_matrix = wu.compute_wals_cp_matrix_from_general_data(
                            self.language_parameters[lpn2].parameter_pk,
                            self.language_parameters[lpn1].parameter_pk
                        )
                        self.graph[lpn1][lpn2] = cp_matrix
                    elif lpn1 in gu.grambank_pid_by_pname.keys() and lpn2 in gu.grambank_pid_by_pname.keys() and lpn2 != lpn1:
                        cp_matrix = gu.compute_grambank_cp_matrix_from_general_data(
                            self.language_parameters[lpn2].parameter_pk,
                            self.language_parameters[lpn1].parameter_pk
                        )
                        self.graph[lpn1][lpn2] = cp_matrix

                    # grambank base node to wals node, value is wals given grambank
                    elif lpn1 in gu.grambank_pid_by_pname.keys() and lpn2 in wu.parameter_pk_by_name.keys():
                        cp_matrix = gwu.compute_wals_given_grambank_cp(self.language_parameters[lpn2].parameter_pk,
                                                                       self.language_parameters[lpn1].parameter_pk)
                        if cp_matrix is not None:
                            self.graph[lpn1][lpn2] = cp_matrix

                    # wals given grambank
                    elif lpn1 in wu.parameter_pk_by_name.keys() and lpn2 in gu.grambank_pid_by_pname.keys():
                        cp_matrix = gwu.compute_grambank_given_wals_cp(self.language_parameters[lpn2].parameter_pk,
                                                                       self.language_parameters[lpn1].parameter_pk)
                        if cp_matrix is not None:
                            self.graph[lpn1][lpn2] = cp_matrix
        if self.verbose:
            print("Agent {}: Graph initialized.".format(self.name))

    def initialize_grambank_list_of_language_pks_used_for_statistics(self):
        language_pks_used_for_statistics = []
        # TODO: Handle language family filter
        language_pks_used_for_statistics = list(gu.grambank_language_by_lid.keys())
        if self.verbose:
            print("Agent {}: {} grambank languages used for statistics.".format(self.name,
                                                                       len(language_pks_used_for_statistics)))
        return language_pks_used_for_statistics

    def initialize_wals_list_of_language_pks_used_for_statistics(self):
        language_pks_used_for_statistics = []
        if self.language_stat_filters != {}:
            if "family" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["family"]:
                    language_pks_used_for_statistics += wu.get_language_pks_by_family(f)
            if "subfamily" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["subfamily"]:
                    language_pks_used_for_statistics +=  wu.get_language_pks_by_subfamily(f)
            if "genus" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["genus"]:
                    language_pks_used_for_statistics += wu.get_language_pks_by_genus(f)
            if "macroarea" in self.language_stat_filters.keys():
                for f in self.language_stat_filters["macroarea"]:
                    language_pks_used_for_statistics += wu.get_language_pks_by_macroarea(f)
            language_pks_used_for_statistics = list(set(language_pks_used_for_statistics))
        else:
            language_pks_used_for_statistics = list(wu.language_by_pk.keys())
        if self.verbose:
            print("Agent {}: {} wals languages used for statistics.".format(self.name, len(language_pks_used_for_statistics)))
        return language_pks_used_for_statistics

    def run_belief_update_from_observations(self):
        path = self.create_random_propagation_path()
        # update each parameter's beliefs from observations and neighbors messages
        for p_name in path:
            self.language_parameters[p_name].update_beliefs_from_observations()

    def run_belief_update_cycle(self):
        path = self.create_random_propagation_path()
        # run messaging round
        self.run_message_round()
        # update each parameter's beliefs from observations and neighbors messages
        for p_name in path:
            self.language_parameters[p_name].update_beliefs_from_observations()
            self.update_beliefs_from_messages_received(p_name)

    def run_message_round(self):
        messages = {}
        path = self.create_random_propagation_path()
        for sender_name in path:
            for recipient_name in self.graph[sender_name].keys():
                message = self.generate_message(sender_name, recipient_name)
                self.language_parameters[recipient_name].message_inbox[sender_name] = message
                messages[sender_name + "->" + recipient_name] = message
                # if self.verbose:
                #     print("Message {}->{}: {}".format(sender_name, recipient_name, message))
    def create_random_propagation_path(self):
        """ List of parameters indicating the order in which the belief propagation is executed."""
        path = self.parameter_names.copy()
        random.shuffle(path)
        if self.verbose:
            print("General Agent {}: Random belief propagation path is {}".format(self.name, path))
        return path

    def add_observations(self, parameter_name, observations):
        """ add observations to a LanguageParameter observation inbox.
        Observations are {'depk':number of occurrences}
        example:
        observations = {'387': 0, '386': 0, '388': 0, '385': 8, '383': 2, '384': 0, '389': 0}
        gawo.add_observations("Order of Subject, Object and Verb", observations)"""
        if self.verbose:
            print("Agent {}: adding observation {} to LanguageParameter {}.".format(self.name, observations, parameter_name))
        if parameter_name in self.language_parameters.keys():
            self.language_parameters[parameter_name].observations_inbox.append(observations)

    def update_beliefs_from_messages_received(self, parameter_name, verbose=False):
        """
        Updates the beliefs of a parameter based on messages received from neighbors.

        Parameters:
        - parameter_name: Name of the parameter (node) to update.

        Returns:
        - None (the function updates the beliefs in place).
        """
        if verbose:
            print("Agent {}: update_beliefs_from_messages_received({})".format(self.name, parameter_name))
            print("Initial belief: {}".format(self.language_parameters[parameter_name].beliefs))
        # Retrieve the parameter object
        P = self.language_parameters[parameter_name]

        # update beliefs only if the parameter is not locked
        if P.locked is False:

            # Get the messages from neighbors
            message_inbox = P.message_inbox  # {neighbor_name: message_dict}

            # Initialize new beliefs
            new_beliefs = {}

            # Get the possible values of x_i
            x_i_values = P.beliefs.keys()

            for x_i in x_i_values:
                # Start with local evidence
                belief = P.beliefs.get(x_i, 1.0)  # Default to 1.0 if local evidence is missing

                # Multiply by messages from all neighbors
                for neighbor_name, message in message_inbox.items():
                    m_neighbor_to_P = message  # {x_i: probability}
                    m_value = m_neighbor_to_P.get(x_i, 1.0)  # Default to 1.0 if message value is missing
                    belief *= m_value

                new_beliefs[x_i] = belief

            # Normalize the beliefs
            total_belief = sum(new_beliefs.values())
            if total_belief > 0:
                for x_i in x_i_values:
                    new_beliefs[x_i] /= total_belief
            else:
                # Handle zero total by assigning uniform probabilities
                num_values = len(x_i_values)
                if num_values > 0:
                    uniform_prob = 1.0 / num_values
                    for x_i in x_i_values:
                        new_beliefs[x_i] = uniform_prob

            # Update the beliefs in the parameter object
            P.beliefs = new_beliefs
            P.beliefs_history.append(new_beliefs)
            if verbose:
                print("Agent {}: belief of parameter {} updated)".format(self.name, parameter_name))
                print("New belief: {}".format(self.language_parameters[parameter_name].beliefs))

        else:
            if verbose:
                print("Agent {}: parameter {} is locked and will not be updated by messages.".format(self.name, parameter_name))


    def generate_message(self, Pi_name, Pj_name, verbose=False):
        """
        Generates the message from parameter Pi to parameter Pj using belief propagation.

        Parameters:
        - Pi_name: Name of the sender parameter (node).
        - Pj_name: Name of the recipient parameter (node).

        Returns:
        - A dictionary representing the message {pj_value_code: probability}.
        """
        if verbose:
            print("Agent {}: Generate message {} ---> {}".format(self.name, Pi_name, Pj_name))

        # Retrieve the parameter objects
        Pi = self.language_parameters[Pi_name]
        Pj = self.language_parameters[Pj_name]
        # Get the potential function between Pi and Pj
        cp_matrix_Pj_given_Pi = self.graph[Pi_name][Pj_name]  # DataFrame with rows x_i, columns x_j

        # Get the local evidence (beliefs) at node Pi
        phi_i = Pi.beliefs  # {x_i: probability}

        # Get neighbors of Pi excluding Pj
        neighbors_i = self.graph[Pi_name].keys()
        neighbors_except_j = [k for k in neighbors_i if k != Pj_name]

        # Initialize the product of incoming messages for each x_i
        x_i_values = phi_i.keys()  # Possible values of Pi
        product_messages = {x_i: 1.0 for x_i in x_i_values}

        # Multiply messages from all neighbors except Pj
        for neighbor_name in neighbors_except_j:
            # Get the message from neighbor to Pi
            m_neighbor_to_Pi = Pi.message_inbox.get(neighbor_name, {})
            for x_i in x_i_values:
                # Get the message value, defaulting to 1.0 if not present
                m_value = m_neighbor_to_Pi.get(x_i, 1.0)
                product_messages[x_i] *= m_value

        # Compute the message from Pi to Pj
        x_j_values = Pj.beliefs.keys()  # Possible values of Pj
        message_Pi_to_Pj = {x_j: 0.0 for x_j in x_j_values}

        for x_j in x_j_values:
            total = 0.0
            for x_i in x_i_values:
                # Retrieve values
                phi_i_xi = phi_i.get(x_i, 0.0)
                psi_ij = cp_matrix_Pj_given_Pi.at[x_j, x_i]  # Potential value between x_i and x_j
                prod_msg_xi = product_messages.get(x_i, 1.0)
                # Compute the term
                term = phi_i_xi * psi_ij * prod_msg_xi
                total += term
            message_Pi_to_Pj[x_j] = total

        # Normalize the message
        total_message = sum(message_Pi_to_Pj.values())
        if total_message > 0:
            for x_j in x_j_values:
                message_Pi_to_Pj[x_j] /= total_message
        else:
            # Handle zero total by assigning uniform probabilities or keeping zeros
            num_values = len(x_j_values)
            if num_values > 0:
                uniform_prob = 1.0 / num_values
                for x_j in x_j_values:
                    message_Pi_to_Pj[x_j] = uniform_prob

        if verbose:
            print("Agent {}: Generated message {} ---> {}: {}".format(self.name, Pi_name, Pj_name, message_Pi_to_Pj))
        # Return the computed message
        return message_Pi_to_Pj




