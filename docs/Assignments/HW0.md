Github introduction
====

1. Create a Github.com account
2. Add your account to [google sheet](https://docs.google.com/forms/d/1ocUjG5zQbPa7NaPMfT2zADQox_k_3WE6PcAy4Co796A/edit)
3. read the directions on how to [run visual studio](https://hpcc.ucr.edu/manuals/hpc_cluster/selected_software/vscode/) - this is linked through your github account and allows you to run via the web or have visual studio on your laptop but connect to the hpcc server for file saving and github push/pull/commit commands as well. The goal of homework 1 is for you to practice using these tools even though they are new and maybe a little confusing. You can also just use jupyter notebook for your editing of code if you don't want to try these other things out.

## There is one homework for you to accept:

1. [github intro](https://classroom50.org/biodataprog/gen220/assignments/setup-github-and-classroom/submissions) - this is to learn and practice about github
This is due Oct 1, 2026.

Github practice
===

1. From [first link](https://classroom50.org/biodataprog/gen220/assignments/setup-github-and-classroom/submissions). You should be able to accept this homework once I have your github account. 

2. Read the [Git and GitHub guide](../Resources/Git_tutorial): do the "One-time setup" and "Logging in" sections, then practice Recipe B.

3. Practice using a text editor - VisualStudio can be run on the web - but then you can also use the text editor in jupyter notebook on the https://ondemand.hpcc.ucr.edu. You can also learn how to use command line text editors. See https://hpcc.ucr.edu/manuals/linux_basics/text/ and this on how to setup visual studio for remote edit (so you can run this from you https://hpcc.ucr.edu/manuals/hpc_cluster/selected_software/vscode/)

4. Create SSH keys to login to HPCC (see the [SSH keys guide](../Resources/SSH_keys)). You will also want to setup [SSH-keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) or [github tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) for you to be able to do the checkins to the cluster. 

For setting up github ssh keys it isn't too hard but you will need to make sure that key is on the computer you running/connecting from. You can add more than one key to your account but that should include one from your laptop and the hpcc. 

4. In your created github repository after you have accepted the assignment, create a file called 'README.md' and add some information about the name of the organisms you work on. you can do this on the web.

5. Checkout the repository locally (on your command line `git clone git@github.com:biodataprog/gen220-setup-github-and-classroom-hyphaltip`). You can run that on your laptop or on the cluster.  
    * Next add a file in that folder. Add this to the repository `git add FILE.txt`.
    * Now you can commit it with `git commit -m "this is a message" FILE.txt"` 
    * Now you sync your copy from your computer to github `git push`

There are some instructions throughout on github about using this but we will also practice this in class a few times so if you don't succeed it is okay for the homewok purposes.
