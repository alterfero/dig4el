import json
from libs import wals_utils as wu
import math

# GLOBAL VARIABLES
with open("./external_data/wals_derived/domain_elements_pk_by_parameter_pk_lookup_table.json") as f:
    domain_elements_pk_by_parameter_pk = json.load(f)
with open("./external_data/wals_derived/parameter_pk_by_name_filtered.json") as f:
    parameter_pk_by_name_filtered = json.load(f)

class LanguageParameter:
    def __init__(self, parameter_name, target_language_name, priors_language_pk_list = [], verbose=True):
        self.verbose = verbose
        self.name = parameter_name
        self.target_language_name = target_language_name
        self.target_language_in_wals = False
        self.priors_language_pk_list = priors_language_pk_list

        # a locked boolean is used for parameters with known value.
        self.locked = False
        if self.verbose:
            print("Language Parameter {} initialization, verbose is on.".format(self.name))
        # param pk
        if parameter_name in wu.parameter_pk_by_name:
            self.parameter_pk = str(wu.parameter_pk_by_name[parameter_name])
        else:
            self.parameter_pk = "none"
        # target language in wals
        if self.target_language_name in wu.language_pk_id_by_name.keys():
            self.target_language_in_wals = True
            if self.verbose:
                print("Language Parameter {}: Target language {} is in WALS.".format(self.name, self.target_language_name))
        # values
        if self.parameter_pk in domain_elements_pk_by_parameter_pk:
            self.values = domain_elements_pk_by_parameter_pk[self.parameter_pk]
        else:
            self.values = []
        # beliefs
        self.beliefs = {}

    def initialize_beliefs_with_wals(self):
        depks = domain_elements_pk_by_parameter_pk[self.parameter_pk]
        # initialize with statistical priors
        self.beliefs = wu.compute_param_distribution(self.parameter_pk,
                                                            self.priors_language_pk_list)
        if self.verbose:
            print("LanguageParameter {}: Beliefs initialized with WALS: {}".format(self.name, self.beliefs))

    def update_beliefs_from_observations(self, observations, influence_distribution = "uniform", observation_influence=0.6, verbose=True):
        """this function takes a dict of observation counts of the values of the said parameter
        and uses it to update the corresponding uncertain variable.
        observations is of the form {value1: count1, value2: count2...}"""
        #TODO Implement non uniform influence distribution
        # check if the observations given include all the values
        if verbose:
            print("LanguageParameter {}: Updating current beliefs with observations".format(self.name))
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
            if verbose:
                print("LanguageParameter {}: posteriors: {}".format(self.name, posteriors))

class GeneralAgent:
    """ A general agent looks at a set of parameters independently of constructions.
    by default, all parameters a general agent observe are considered as nodes of a non-directed,
    fully connected graph."""
    def __init__(self, name, target_language_name, parameter_names=[], language_stat_filter={}, verbose=True):
        self.verbose = verbose
        if self.verbose:
            print("General Agent {} initialization, verbose is on.".format(name))
        self.name = name
        self.target_language = target_language_name
        self.language_stat_filters = language_stat_filter
        self.target_language_in_wals = False
        self.language_pks_used_for_statistics = []
        # the different parameters the general agent is focusing on
        self.parameter_names = parameter_names
        self.language_parameters = {}

        # populate language_pks_used_for_statistics
        self.initialize_list_of_language_pks_used_for_statistics()

        # create and initialize instances of LanguageParameters objects
        for parameter_name in self.parameter_names:
            if parameter_name in wu.parameter_pk_by_name:
                new_language_parameter = LanguageParameter(parameter_name, self.target_language, self.language_pks_used_for_statistics)
                self.language_parameters[parameter_name] = new_language_parameter
                new_language_parameter.initialize_beliefs_with_wals()
            else:
                print("General Agent {}: parameter name {} not in parameter_pk_by_name, discarding.".format(self.name, parameter_name))
        if verbose:
            print("General Agent {}: {} instances of LanguageParameter objects initialized.".format(self.name, len(self.language_parameters)))

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

    def update_beliefs_from_observations(self, parameter_name, observations, influence_distribution = "uniform", observation_influence=0.6, verbose=True):
        """ ask a one of its LanguageParameter to update its beliefs based on new observations."""
        if verbose:
            print("Agent {}: asking LanguageParameter {} to update its beliefs based on observation {}.".format(self.name, parameter_name, observations))
        if parameter_name in self.language_parameters.keys():
            self.language_parameters[parameter_name].update_beliefs_from_observations(observations, influence_distribution, observation_influence, verbose)





