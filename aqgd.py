# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Analytic Quantum Gradient Descent (AQGD) optimizer."""

from copy import deepcopy
from numpy import pi, absolute, array, zeros


class AQGD:
    """Analytic Quantum Gradient Descent (AQGD) optimizer class.
    Performs optimization by gradient descent where gradients
    are evaluated "analytically" using the quantum circuit evaluating
    the objective function.
    """

    def __init__(self, maxiter=1000, eta=3.0, tol=1e-6, disp=False, momentum=0.25):
        """
        Constructor.
        Performs Analytical Quantum Gradient Descent (AQGD).
        Args:
            maxiter (int): Maximum number of iterations, each iteration evaluation gradient.
            eta (float): The coefficient of the gradient update. Increasing this value
                         results in larger step sizes: param = previous_param - eta * deriv
            tol (float): The convergence criteria that must be reached before stopping.
                         Optimization stops when: absolute(loss - previous_loss) < tol
            disp (bool): Set to true to display convergence messages.
            momentum (float): Bias towards the previous gradient momentum in current update.
                              Must be within the bounds: [0,1)
        """
        self._eta = eta
        self._maxiter = maxiter
        self._tol = tol if tol is not None else 1e-6
        self._disp = disp
        self._momentum_coeff = momentum

    def deriv(self, j, params, obj):
        """
        Obtains the analytical quantum derivative of the objective function with
        respect to the jth parameter.
        Args:
            j (int): Index of the parameter to compute the derivative of.
            params (array): Current value of the parameters to evaluate
                            the objective function at.
            obj (callable): Objective function.
        Returns:
            float: The derivative of the objective function w.r.t. j
        """
        # create a copy of the parameters with the positive shift
        plus_params = deepcopy(list(params))
        plus_params[j] += pi / 2
        obj_plus = obj(plus_params)

        # create a copy of the parameters with the negative shift
        minus_params = deepcopy(list(params))
        minus_params[j] -= pi / 2
        obj_minus = obj(minus_params)
        
        # TODO: If obj_plus or obj_minus is small, return the parameters at that point
        

        # return the derivative value
        return 0.5 * (obj_plus - obj_minus)

    def update(self, j, params, deriv, mprev):
        """
        Updates the jth parameter based on the derivative and previous momentum
        Args:
            j (int): Index of the parameter to compute the derivative of.
            params (array): Current value of the parameters to evaluate
                            the objective function at.
            deriv (float): Value of the derivative w.r.t. the jth parameter
            mprev (array): Array containing all of the parameter momentums
        Returns:
            tuple: params, new momentums
        """
        mnew = self._eta * (deriv * (1-self._momentum_coeff) + mprev[j] * self._momentum_coeff)
        params[j] -= mnew
        params[j] = params[j] % (2 * pi)
        return params, mnew

    def converged(self, objval, n=2):
        """
        Determines if the objective function has converged by finding the difference between
        the current value and the previous n values.
        Args:
            objval (float): Current value of the objective function.
            n (int): Number of previous steps which must be within the convergence criteria
                     in order to be considered converged. Using a larger number will prevent
                     the optimizer from stopping early.
        Returns:
            bool: Whether or not the optimization has converged.
        """
        self._previous_loss = [objval + 2 * self._tol] * n

        if all([absolute(objval - prev) < self._tol for prev in self._previous_loss]):
            # converged
            return True

        return False

    def optimize(self, x0, objective_function, gradient_function=None,
                 variable_bounds=None):
        num_vars = len(x0)
        params = deepcopy(x0)
        it = 0
        momentum = [0] * num_vars
        objval = objective_function(params)

        if self._disp:
            print(f"Iteration: {it}\t| Energy: {objval}\t| Params: {params}")

        minobj = objval
        minparams = params

        while it < self._maxiter and not self.converged(objval):
            for j in range(num_vars):
                # update parameters in order based on quantum gradient
                derivative = self.deriv(j, params, objective_function)
                params, momentum[j] = self.update(j, params, derivative, momentum)

            # Compute the value of the objective function
            objval = objective_function(params)

            # Keep the best parameters
            if objval < minobj:
                minobj = objval
                minparams = params

            # update the iteration count
            it += 1
            if self._disp:
                print(f"Iteration: {it}\t| Energy: {objval}\t| Params: {params}")

        return minparams, minobj, it