UNIX practice
====

On the UNIX command line. Go into your bigdata folder. If you have not used the cluster before then you will be in the `gen220` project. Or you may have your own lab bigdata folder.

See [Text Editors in UNIX](https://hpcc.ucr.edu/manuals/linux_basics/text/)
While it takes a few steps to install and setup, [VisualStudio](https://code.visualstudio.com/download) is a great resource
you can edit on your local machine but saves changes on HPCC. See <https://hpcc.ucr.edu/manuals/hpc_cluster/selected_software/vscode/>

__This should work__

```bash
cd ~/bigdata
```

__but if it doesn't__

```bash
cd /bigdata/gen220/$USER # will go into your bigdata folder for the class
```

__But if you already had an account on the cluster then__

```bash
# if the above doesn't work you are likely already in a lab group on HPCC
cd /bigdata/$GROUP/$USER # should work since $USER is your login and $GROUP is your primary lab group
# you can see what groups you are in by typing
groups
```


For your homework:

1. Accept the homework 1 problem - (see link in Canvas). 
2. Create a folder to work in on HPCC (or your own computer): `mkdir -p ~/bigdata/gen220/homework` and then `cd  ~/bigdata/gen220/homework`
3. Checkout the GEN220 data folder `git clone https://github.com/biodataprog/GEN220_data.git`

   Now you want to make a folder for your work for this class

   The steps look like this:

   ```bash
   # you can make a folder for GEN220
   mkdir gen220
   # go into that folder
   cd gen220
   # now use git to checkout the class data folder
   git clone https://github.com/biodataprog/GEN220_data.git
   # now go into this folder
   cd GEN220_data
   ```

   Look around in the folder. Go into the `tabular` folder where I've stored some tab or comma delimited data.  You will later need to copy a file from this folder into your homework folder.

4. Checkout the homework 1 github repository created in step 1 (if you [setup SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account) in github)

   ```bash
   git clone git@github.com:biodataprog/2026-hw1-YOURGITHUBID.git
   ```

   OR for the https will need to [create a token as your password](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

   ```bash
   git clone https://github.com/biodataprog/2026-hw1-YOURGITHUBID.git
   ```

5. Go into your folder (`cd 2026-hw1-YOURGITHUBID`).

6. Edit a script in there called `filesize.sh`; you can do this in jupyter on web, you can edit on the command line with `nano`, `vi`, or `emacs`, or you can [use visual studio tunnel](https://docs.google.com/presentation/d/1pEXb4H47atpWruV0qxoYcZxtLc3dPk9ehIXNkf8Zv1g/edit)
7. Add some code to this script which achieves the directions at the bottom of this page
8. Test it out (run the `./filesize.sh`).
9. To submit your homework (and you can do this more than once), this requires doing `git commit` and then `git push`

   ```bash
   # this step saves a version of the code
   git commit -m "This is a homework 1 solution" filesize.sh
   # this step will push the data from HPCC or your computer UP to the github site
   # this step will request your username (YOURGITHUBID) and your password (that TOKEN I mentioned before).
   # if you have setup github account with SSH keys then it will ask you for your SSH key password
   git push
   ```

10. You can repeat doing edits to the file, commit, and push to github.

Tasks for Homework 1
====

1. copy the `threatened-species.csv.gz` file - see info here [HW1](https://biodataprog.github.io/GEN220_2026/Assignments/HW1) or you can just run the included `./setup.sh` script to download. but also encourage you to practice with `cp` command.
2. Write a script called `answer1.sh`:
   * print out the size of the threatened-species.csv.gz using `du` or `ls -l`
   * Count the number of lines in file
   * Print out the number of unique phyla, order_name in the table using `cut`, `sort`, `uniq`
   * count how many kingdom FUNGI are present in the file?
3. Check in your changes with `git commit -m 'a message'` and `git push` to save the changes to github.
