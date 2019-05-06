# Prequisites
# 1) You must have devstack up and running
# 2) You must have hub installed (brew install hub)
# 3) You must have a publickey set up with github (so hub can make your PR)

# How To Run
# 1) Have devstack up and running (via `make dev.up` in your devstack repo)
# 2) On the command line, go into your edx-platform repo checkout
# 3) Make sure you are on the master branchof edx-platform with no changes
# 4) Run this script from the root of the repo, handing it your username, ticketname, and subdirectory to convert:
#     ./scripts/py2_to_py3_convert_and_create_pr.sh cpappas INCR-1234 common/lib/xmodule

help_text="\nUsage: ./scripts/py2_to_py3_convert_and_create_pr.sh <username> <ticket-name> <subdirectory>\n";
help_text+="Example: ./scripts/py2_to_py3_convert_and_create_pr.sh cpappas INCR-1234 common/lib/xmodule\n\n";

for i in "$@" ; do
    if [[ $i == "--help" ]] ; then
        printf "$help_text";
        exit 0;
    fi
done

if [[ $# -lt 3 ]]; then
	printf "$help_text";
	exit 0;
fi

myname="$1";
myticket="$2";
subdirectory="$3";

mybranch="$myname/$myticket";

git checkout -b $mybranch || { printf "\n\nERROR: could not check out branch with name: $mybranch\n\n"; exit 1; }
docker exec -t edx.devstack.lms bash -c "source /edx/app/edxapp/edxapp_env && cd /edx/app/edxapp/edx-platform/ && python-modernize -w $subdirectory && pytest $subdirectory" || { printf "\n\nERROR: Tests did not pass, or something went wrong trying to run tests.\n\n"; exit 1; }
git add $subdirectory || { printf "\n\nERROR: Could not 'git add' directory $subdirectory\n\n"; exit 1; }
git commit -m"$mybranch" || { printf "\n\nERROR: Could not commit files to $mybranch\n\n"; exit 1; }
git push origin "$mybranch" || { printf "\n\nERROR: Could not push branch to remote. If you are outside of the edX organization, you might consider first forking the repo, and then running this command to create a PR from within that checkout.\n\n"; exit 1; }
hub pull-request -m"$myticket" || { printf "\n\nERROR: Did not successfully create PR for this conversion\n\n"; }
