FROM node:22-bookworm

# System packages: git, pdflatex (texlive), build tools for dasm, Maven for ghidra-mcp
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    maven \
    wget \
    unzip \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install JDK 21 from Adoptium (not available in Bookworm repos)
# Map dpkg arch to Adoptium arch naming (arm64 -> aarch64)
RUN ARCH=$(dpkg --print-architecture) \
    && if [ "$ARCH" = "arm64" ]; then ARCH="aarch64"; fi \
    && curl -sL "https://api.adoptium.net/v3/binary/latest/21/ga/linux/${ARCH}/jdk/hotspot/normal/eclipse" -o /tmp/jdk21.tar.gz \
    && mkdir -p /opt/java \
    && tar -xzf /tmp/jdk21.tar.gz -C /opt/java --strip-components=1 \
    && rm /tmp/jdk21.tar.gz
ENV JAVA_HOME="/opt/java"
ENV PATH="/opt/java/bin:${PATH}"

# Install Ghidra 12.0.3
RUN wget -q https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.0.3_build/ghidra_12.0.3_PUBLIC_20260210.zip -O /tmp/ghidra.zip \
    && unzip -q /tmp/ghidra.zip -d /opt \
    && ln -s /opt/ghidra_12.0.3_PUBLIC /opt/ghidra \
    && rm /tmp/ghidra.zip
ENV PATH="/opt/ghidra:${PATH}"

# Install ghidra-mcp extension
RUN git clone https://github.com/bethington/ghidra-mcp.git /tmp/ghidra-mcp \
    && cd /tmp/ghidra-mcp \
    && ./ghidra-mcp-setup.sh --preflight --ghidra-path /opt/ghidra_12.0.3_PUBLIC \
    && ./ghidra-mcp-setup.sh --deploy --ghidra-path /opt/ghidra_12.0.3_PUBLIC \
    && pip3 install --break-system-packages -r /opt/ghidra_12.0.3_PUBLIC/requirements.txt \
    && sed -i 's/if parsed.hostname in \["localhost", "127.0.0.1", "::1"\]/if parsed.hostname in ["localhost", "127.0.0.1", "::1", "host.docker.internal"]/' /opt/ghidra_12.0.3_PUBLIC/bridge_mcp_ghidra.py \
    && rm -rf /tmp/ghidra-mcp

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for weave.py
RUN pip3 install --break-system-packages absl-py

# Build dasm from source
RUN git clone https://github.com/dasm-assembler/dasm.git /tmp/dasm \
    && cd /tmp/dasm \
    && make \
    && cp /tmp/dasm/bin/dasm /usr/local/bin/dasm \
    && rm -rf /tmp/dasm

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Entrypoint ensures ghidra-mcp config is in Claude Code settings
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user for Claude Code --dangerously-skip-permissions
RUN useradd -m -s /bin/bash robertbaruch \
    && mkdir -p /home/robertbaruch/.claude \
    && chown -R robertbaruch:robertbaruch /home/robertbaruch/.claude \
    && echo 'alias yolo="claude --dangerously-skip-permissions"' >> /home/robertbaruch/.bashrc
USER robertbaruch

WORKDIR /project

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["bash"]
