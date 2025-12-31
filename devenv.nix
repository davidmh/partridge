{ pkgs, ... }:

{
  devenv.warnOnNewVersion = false;

  languages.python = {
    enable = true;
    uv.enable = true;
    version = "3.14";
  };

  packages = with pkgs; [
    graphviz # Provides the dot command to build the dependency graph
  ];
}
