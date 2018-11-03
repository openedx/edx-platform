FROM python:latest
ARG PACKAGES
RUN pip install --upgrade pip &&  pip install nbgrader
RUN python3 -m venv /home/temp_env
RUN /home/temp_env/bin/pip install $PACKAGES
RUN /home/temp_env/bin/python -m ipykernel install --prefix=/usr/local/ --name="temp_env"
RUN mkdir -p /home/nbgrader/course/source/ps1 && \
    mkdir -p /etc/jupyter
COPY container.py run_grader.py autograded_checkers.py exceptions.py /home/jupyter/
