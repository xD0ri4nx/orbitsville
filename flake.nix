{
  description = "Orbitsville Lunar EME Cyberdeck Terminal Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        pythonEnv = pkgs.python3.withPackages (ps: [
          ps.requests
          ps.websockets
          ps.ephem
        ]);

        deckRunner = pkgs.writeShellScriptBin "orbitsville-deck" ''
          set -e

          echo ">> Initializing PulseAudio Virtual Audio Bus..."
          ${pkgs.pulseaudio}/bin/pulseaudio --start --exit-idle-time=-1 2>/dev/null || true
          # Create virtual loopback sink
          MODULE_ID=$(${pkgs.pulseaudio}/bin/pactl load-module module-null-sink \
            sink_name=lunar_sink \
            sink_properties=device.description=LunarEME 2>/dev/null || true)
          ${pkgs.pulseaudio}/bin/pactl set-sink-volume lunar_sink 30% 2>/dev/null || true

          cleanup() {
            echo ">> Terminating Orbitsville Stack..."
            ${pkgs.tmux}/bin/tmux kill-session -t orbitsville 2>/dev/null || true
            if [ -n "$MODULE_ID" ]; then
              ${pkgs.pulseaudio}/bin/pactl unload-module "$MODULE_ID" 2>/dev/null || true
            fi
            kill $(jobs -p) 2>/dev/null || true
          }
          trap cleanup EXIT INT TERM

          SCRIPT_DIR="$(pwd)/scripts"

          echo ">> Starting Headless WebSDR Audio Bridge..."
          ${pythonEnv}/bin/python3 "$SCRIPT_DIR/websdr_pull.py" | \
            ${pkgs.pulseaudio}/bin/pacat -p -d lunar_sink --format=s16le --rate=8000 --channels=1 &

          echo ">> Launching WSJT-X background decoder..."
          ${pkgs.wsjtx}/bin/wsjtx &

          echo ">> Spawning CRT Terminal Matrix..."
          # Start tmux session detached, configure 3-pane layout, then attach via cool-retro-term
          ${pkgs.tmux}/bin/tmux new-session -d -s orbitsville \
            "${pythonEnv}/bin/python3 $SCRIPT_DIR/orbitsville_terminal.py"
          
          # Split horizontally (creates right column)
          ${pkgs.tmux}/bin/tmux split-window -h -t orbitsville \
            "${pythonEnv}/bin/python3 $SCRIPT_DIR/track_moon.py"
          
          # Split bottom right pane vertically
          ${pkgs.tmux}/bin/tmux split-window -v -t orbitsville:0.1 \
            "${pythonEnv}/bin/python3 $SCRIPT_DIR/lunar_radar.py"

          # Focus the terminal output pane
          ${pkgs.tmux}/bin/tmux select-pane -t orbitsville:0.0

          # Launch cool-retro-term attached to the configured tmux session
          ${pkgs.cool-retro-term}/bin/cool-retro-term -e ${pkgs.tmux}/bin/tmux attach-session -t orbitsville

          wait
        '';

      in {
        # 'nix develop' for manual debugging
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            pythonEnv
            pulseaudio
            pavucontrol
            wsjtx
            tmux
            cool-retro-term
          ];
        };

        # 'nix run' boots the whole deck
        apps.default = {
          type = "app";
          program = "${deckRunner}/bin/orbitsville-deck";
        };
      }
    );
}

