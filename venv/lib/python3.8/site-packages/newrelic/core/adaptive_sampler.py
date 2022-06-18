# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import time
import threading


class AdaptiveSampler(object):
    def __init__(self, sampling_target, sampling_period):
        self.adaptive_target = 0.0
        self.period = sampling_period
        self.last_reset = time.time()
        self._lock = threading.Lock()

        # For the first harvest, collect a max of sampling_target number of
        # "sampled" transactions.
        self.sampling_target = sampling_target
        self.max_sampled = sampling_target
        self.computed_count_last = sampling_target

        self.computed_count = 0
        self.sampled_count = 0

    def reset_if_required(self):
        time_since_last_reset = time.time() - self.last_reset
        cycles = time_since_last_reset // self.period
        if cycles:
            self._reset()
            # If more than one cycle has passed we need to reset twice to set
            # the computed_count = 0
            if cycles > 1:
                self._reset()

    def compute_sampled(self):
        with self._lock:
            self.reset_if_required()
            if self.sampled_count >= self.max_sampled:
                return False

            elif self.sampled_count < self.sampling_target:
                sampled = random.randrange(
                        self.computed_count_last) < self.sampling_target
                if sampled:
                    self.sampled_count += 1
            else:
                sampled = random.randrange(
                        self.computed_count) < self.adaptive_target
                if sampled:
                    self.sampled_count += 1

                    ratio = float(self.sampling_target) / self.sampled_count
                    self.adaptive_target = (self.sampling_target ** ratio -
                                            self.sampling_target ** 0.5)

            self.computed_count += 1
        return sampled

    def _reset(self):
        # For subsequent harvests, collect a max of twice the
        # self.sampling_target value.
        self.last_reset = time.time()
        self.max_sampled = 2 * self.sampling_target
        self.adaptive_target = (self.sampling_target -
                                self.sampling_target ** 0.5)

        self.computed_count_last = max(self.computed_count,
                                       self.sampling_target)
        self.computed_count = 0
        self.sampled_count = 0
