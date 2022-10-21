library(data.table)
library(ggplot2)
library(stringr)

main <- function(){
  
  file_in <- "./simulation.csv"
  output_folder <- "./"
  rounds <- c(5, 10, 15, 20, 25, 30, 40)
  
  # Read in data.table
  dt <- fread(file_in)
  
  # Find all params
  params <- str_replace_all(names(dt)[str_detect(names(dt), "(?<=mean_)")], "mean_", "")

  
  dt[, optimization := paste("Method: ", optimization)]
  dt[, round_no := round_no + 1]
  

  plot_mse(dt, params, output_folder, rounds)
  plot_timing(dt, output_folder)
  
}

plot_mse <- function(dt, params, output_folder, rounds){
  
  for (param in params){
    
    # Specify column names specific to `param`
    new_col_name <- paste("squared_error", param, sep="_")
    
    estimate_column <- paste("mean", param, sep="_")
    true_column <- paste("true", param, sep="_")
    
    # Compute difference between estimate and true value
    dt[, (new_col_name) := (get(estimate_column) - get(true_column))^2]
    
    # Average MSE if guessing mean true value
    mse_mean_population = dt[, mean((get(true_column) - mean(get(true_column)))^2)]
    
    ggplot(dt, aes(round_no, get(new_col_name), color=optimization)) +
      geom_smooth(se=T) +
      labs(
        title = "Mean squared error by round",
        subtitle = paste("Parameter:", param, sep=" "),
        x = "Round Number",
        y = paste("MSE", param)
      )
    
    file_name <- paste0(output_folder, "figure_", param, ".png")
    ggsave(file_name)
    
    ggplot(dt[round_no %in% rounds], aes(get(true_column), get(estimate_column))) +
      geom_point() +
      geom_smooth(method='lm') +
      geom_abline(slope=1, intercept=0) +
      labs(
        title = "Scatterplot: Estimate vs. True",
        subtitle = paste0("Parameter:", param, sep=" "),
        x = "True Value",
        y = "Estimate"       
      ) +
      facet_grid(optimization~round_no)
    
    file_name_scatter <- paste0(output_folder, "scatter_", param, ".png")
    ggsave(file_name_scatter)
    
    # Save image
    
  }
  
}

plot_timing <- function(dt, output_folder){
  
  mean_dt <- dt[, .(mean_time=mean(time_round)), by=.(optimization)]
  
  ggplot(mean_dt) +
    geom_histogram(aes(optimization, mean_time, fill=optimization), stat='identity') +
    labs(
      title="Average time per round by optimization method",
      x="Optimization Method",
      y="Average Time (s)"
    )
  
  file_name <- paste0(output_folder, "timing_figure.png")
  ggsave(file_name)
}

################
### EXECUTE ####
################

main()