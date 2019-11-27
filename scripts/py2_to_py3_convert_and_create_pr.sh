# Prequisites
# 1) You must have devstack up and running
# 2) You must have hub installed (brew install hub)
# 3) You must have a publickey set up with github (so hub can make your PR)
# 4) You must have run the script here https://github.com/edx/testeng-ci/blob/master/scripts/create_incr_tickets.py
#    in order to generate an input file used for bulk creation of INCR tickets

# How To Run
# 1) Have devstack up and running (via `make dev.up` in your devstack repo)
# 2) On the command line, go into your edx-platform repo checkout
# 3) Make sure you are on the master branchof edx-platform with no changes
# 4) Run this script from the root of the repo, handing it your username, and
#    the path to the input file generated in the prerequisites.
# Example usage
#     ./scripts/py2_to_py3_convert_and_create_pr.sh cpappas ~/testeng-ci/scripts/output.csv

help_text="\nUsage: ./scripts/py2_to_py3_convert_and_create_pr.sh <username> <path to input file>\n";
help_text+="Example: ./scripts/py2_to_py3_convert_and_create_pr.sh cpappas ~/testeng-ci/scripts/output.csv\n\n";

for i in "$@" ; do
    if [[ $i == "--help" ]] ; then
        printf "$help_text";
        exit 0;
    fi
done

if [[ $# -lt 2 ]]; then
    printf "$help_text";
    exit 0;
fi

# the github user account that will be used to create these PRs
github_user="$1";
# filepath of the csv file
input_file="$2";


while read line; do

    # Given the following line from the input file:
    # INCR-233,False,14,lms/djangoapps/shoppingcart/management:lms/djangoapps/shoppingcart/tests
    # the ticket number should be: 'INCR-233'
    # the directories to modernize should be "lms/djangoapps/shoppingcart/management lms/djangoapps/shoppingcart/tests"
    ticket_number=`echo $line |cut -d',' -f1`;
    directories=`echo $line |cut -d',' -f4 |tr ':' ' '`;
    branch_name="$github_user/$ticket_number";

    # make sure we are based on master for each consecutive new pull request we create
    git checkout master;

    # create a new branch for this INCR ticket
    git checkout -b $branch_name || { printf "\n\nERROR: could not check out branch with name: $branch_name\n\n"; exit 1; }

    # run python modernize on the specified directories
    docker exec -t edx.devstack.lms bash -c "source /edx/app/edxapp/edxapp_env && cd /edx/app/edxapp/edx-platform/ && python-modernize -w $directories"

    # commit the changes from running python-modernize
    git add $directories || { printf "\n\nERROR: Could not 'git add' directory $directories\n\n"; exit 1; }
    git commit -m "run python modernize" || { printf "\n\nERROR: Could not commit files to $branch_name\n\n"; exit 1; }

    # run isort on the specified directories
    docker exec -t edx.devstack.lms bash -c "source /edx/app/edxapp/edxapp_env && cd /edx/app/edxapp/edx-platform/ && isort -rc $directories"

    # commit the changes from running isort
    git add $directories || { printf "\n\nERROR: Could not 'git add' directory $directories\n\n"; exit 1; }
    git commit -m "run isort" || { printf "\n\nERROR: Could not commit files to $branch_name\n\n"; exit 1; }

    git push origin "$branch_name" || { printf "\n\nERROR: Could not push branch to remote. If you are outside of the edX organization, you might consider first forking the repo, and then running this command to create a PR from within that checkout.\n\n"; exit 1; }

    hub pull-request -m "$ticket_number" || { printf "\n\nERROR: Did not successfully create PR for this conversion\n\n"; }

    # avoid hitting the Github rate limit
    sleep 2

done < $input_file
