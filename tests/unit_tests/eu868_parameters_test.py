"""
Automated testing of the EU868 region parameter definition.
"""
#################################################################################
# MIT License
#
# Copyright (c) 2018, Pablo D. Modernell, Universitat Oberta de Catalunya (UOC).
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################
import pytest
import lorawan.lorawan_parameters.general
import lorawan.lorawan_parameters.testing


@pytest.mark.parameters
class TestDrOffsetEU868(object):
    """
    Tests the data rate offset auxiliary function.
    lorawan.lorawan_parameters.general.rx_dr_offset calculates the new data rate to be used given an initial one
    and a given offset.
    DR0='SF12BW125',
    DR1='SF11BW125',
    DR2='SF10BW125',
    DR3='SF9BW125',
    DR4='SF8BW125',
    DR5='SF7BW125',
    DR6='SF7BW250'
    """
    eu868_expected_results = (
        ('SF12BW125', 0, 'SF12BW125'),
        ('SF12BW125', 1, 'SF11BW125'),
        ('SF12BW125', 2, 'SF10BW125'),
        ('SF12BW125', 3, 'SF9BW125'),
        ('SF12BW125', 4, 'SF8BW125'),
        ('SF12BW125', 5, 'SF7BW125'),
        ('SF11BW125', 0, 'SF11BW125'),
        ('SF11BW125', 1, 'SF10BW125'),
        ('SF11BW125', 2, 'SF9BW125'),
        ('SF11BW125', 3, 'SF8BW125'),
        ('SF11BW125', 4, 'SF7BW125'),
        ('SF11BW125', 5, 'SF7BW250'),
        ('SF10BW125', 0, 'SF10BW125'),
        ('SF10BW125', 1, 'SF9BW125'),
        ('SF10BW125', 2, 'SF8BW125'),
        ('SF10BW125', 3, 'SF7BW125'),
        ('SF10BW125', 4, 'SF7BW250'),
        ('SF10BW125', 5, 'SF7BW250'),
        ('SF9BW125', 0, 'SF9BW125'),
        ('SF9BW125', 1, 'SF8BW125'),
        ('SF9BW125', 2, 'SF7BW125'),
        ('SF9BW125', 3, 'SF7BW250'),
        ('SF9BW125', 4, 'SF7BW250'),
        ('SF9BW125', 5, 'SF7BW250'),
        ('SF8BW125', 0, 'SF8BW125'),
        ('SF8BW125', 1, 'SF7BW125'),
        ('SF8BW125', 2, 'SF7BW250'),
        ('SF8BW125', 3, 'SF7BW250'),
        ('SF8BW125', 4, 'SF7BW250'),
        ('SF8BW125', 5, 'SF7BW250'),
        ('SF7BW125', 0, 'SF7BW125'),
        ('SF7BW125', 1, 'SF7BW250'),
        ('SF7BW125', 2, 'SF7BW250'),
        ('SF7BW125', 3, 'SF7BW250'),
        ('SF7BW125', 4, 'SF7BW250'),
        ('SF7BW125', 5, 'SF7BW250'),
        ('SF7BW250', 0, 'SF7BW250'),
        ('SF7BW250', 1, 'SF7BW250'),
        ('SF7BW250', 2, 'SF7BW250'),
        ('SF7BW250', 3, 'SF7BW250'),
        ('SF7BW250', 4, 'SF7BW250'),
        ('SF7BW250', 5, 'SF7BW250'),
    )

    dr_ids = ["{} with offset {} -> {})".format(t[0], t[1], t[2]) for t in eu868_expected_results]

    @pytest.mark.parametrize('in_dr, offset, expected_dr', eu868_expected_results, ids=dr_ids)
    def test_bytes_nosep(self, in_dr, offset, expected_dr):
        """ Tests the expected result of a data rate offset in EU868."""
        assert lorawan.lorawan_parameters.general.rx_dr_offset(in_dr, offset) == expected_dr


@pytest.mark.parameters
class TestGetDrEU868(object):
    """
    Tests the data rate auxiliary function.
    lorawan.lorawan_parameters.general.get_dr calculates the number of DR given its string representation.
    DR0='SF12BW125',
    DR1='SF11BW125',
    DR2='SF10BW125',
    DR3='SF9BW125',
    DR4='SF8BW125',
    DR5='SF7BW125',
    DR6='SF7BW250'
    """
    eu868_expected_results = (
        ('SF12BW125', 0),
        ('SF11BW125', 1),
        ('SF10BW125', 2),
        ('SF9BW125', 3),
        ('SF8BW125', 4),
        ('SF7BW125', 5),
        ('SF7BW250', 6),
    )

    dr_ids = ["{0} = DR{1} -> {1})".format(t[0], t[1]) for t in eu868_expected_results]

    @pytest.mark.parametrize('in_dr, expected_dr', eu868_expected_results, ids=dr_ids)
    def test_bytes_nosep(self, in_dr, expected_dr):
        """ Tests the expected results of a get data rate in EU868."""
        assert lorawan.lorawan_parameters.general.get_dr(in_dr) == expected_dr
