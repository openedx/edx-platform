# Courtesy of Gregory Nicholas

_subcommand_opts()
{
    local awkfile command cur usage
    command=$1
    cur=${COMP_WORDS[COMP_CWORD]}
    awkfile=/tmp/paver-option-awkscript-$$.awk
    echo '
BEGIN {
    opts = "";
}

{
    for (i = 1; i <= NF; i = i + 1) {
        # Match short options (-a, -S, -3)
        # or long options (--long-option, --another_option)
        # in output from paver help [subcommand]
        if ($i ~ /^(-[A-Za-z0-9]|--[A-Za-z][A-Za-z0-9_-]*)/) {
            opt = $i;
            # remove trailing , and = characters.
            match(opt, "[,=]");
            if (RSTART > 0) {
                opt = substr(opt, 0, RSTART);
            }
            opts = opts " " opt;
        }
    }
}

END {
    print opts
}' > $awkfile

    usage=`paver help $command`
    options=`echo "$usage"|awk -f $awkfile`

    COMPREPLY=( $(compgen -W "$options" -- "$cur") )
}


_paver()
{
    local cur prev
    COMPREPLY=()
    # Variable to hold the current word
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD - 1]}"

    # Build a list of the available tasks from: `paver --help --quiet`
    local cmds=$(paver -hq | awk '/^  ([a-zA-Z][a-zA-Z0-9_]+)/ {print $1}')

    subcmd="${COMP_WORDS[1]}"
    # Generate possible matches and store them in the
    # array variable COMPREPLY

    if [[ -n $subcmd ]]
    then
        case $subcmd in
            test_system)

                _test_system_args
                if [[ -n $COMPREPLY ]]
                then
                    return 0
                fi
                ;;
        esac

        if [[ ${#COMP_WORDS[*]} == 3 ]]
        then
                _subcommand_opts $subcmd
                return 0
        else
            if [[ "$cur" == -* ]]
            then
                _subcommand_opts $subcmd
                return 0
            else
                COMPREPLY=( $(compgen -o nospace -- "$cur") )
            fi
        fi
    fi

    if [[ ${#COMP_WORDS[*]} == 2 ]]
    then
        COMPREPLY=( $(compgen -W "${cmds}" -- "$cur") )
    fi
}

_test_system_args()
{
        local cur prev
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD - 1]}"

        case "$prev" in
            -s|--system)
                COMPREPLY=( $(compgen -W "lms cms" -- "$cur") )
                return 0
                ;;
            *)
                ;;
        esac
}

# Assign the auto-completion function for our command.

complete -F _paver -o default paver
