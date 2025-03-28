sudo apt install -y build-essential libffi-dev libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev liblzma-dev
sudo apt install -y git
git clone https://github.com/pyenv/pyenv.git /usr/local/pyenv

echo 'export PYENV_ROOT="/usr/local/pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc
