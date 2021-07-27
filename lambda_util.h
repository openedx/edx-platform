//
// Copyright 2019 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

#ifndef ZETASQL_ANALYZER_LAMBDA_UTIL_H_
#define ZETASQL_ANALYZER_LAMBDA_UTIL_H_

#include "zetasql/parser/parse_tree.h"
#include "absl/status/status.h"
#include "zetasql/base/statusor.h"

namespace zetasql {

// Validates that the lambda argument list of <ast_lambda> is a list of
// identifiers.
//
// See lambda_parameter_list rule in bison_parser.y about why we cannot simply
// use a list of identifiers.
absl::Status ValidateLambdaArgumentListIsIdentifierList(
    const ASTLambda* ast_lambda);

// Returns the list of lambda argument names.
zetasql_base::StatusOr<std::vector<IdString>> ExtractLambdaArgumentNames(
    const ASTLambda* ast_lambda);

}  // namespace zetasql

#endif  // ZETASQL_ANALYZER_LAMBDA_UTIL_H_
