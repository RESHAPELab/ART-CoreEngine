/**
 * This file is from a project made back in High School. 
 * By Benjamin Carter
 * It represents a single class used in a video game.
 */


package finalV;


import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.event.WindowEvent;

import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JProgressBar;
import javax.swing.border.Border;

public class EasyProgressBar 
{
    public EasyProgressBar( String titlei, String texti, int starti, int mini, int maxi)
    {
    	  title = titlei;
    	  text = texti;
    	  start = starti;
    	  min = mini;
    	  max = maxi;
    	  progressBar = new JProgressBar();
    	  // f = new JFrame(title);
          UnknownClass uc = new UnknownClass();
          uc.screen();
          JFrame f = new JFrame(title);
          f.setSize(1,2);
    }
    public void show()
    {
    	
        f.setDefaultCloseOperation(JFrame.HIDE_ON_CLOSE);
        Container content = f.getContentPane();
        //progressBar = new JProgressBar();
        progressBar.setValue(25);
        progressBar.setStringPainted(true);
        Border border = BorderFactory.createTitledBorder(text);
        progressBar.setBorder(border);
        content.add(progressBar, BorderLayout.NORTH);
        f.setSize(300, 100);
        f.setVisible(true);
        progressBar.setValue(start);
        progressBar.setMinimum(min);
   	    progressBar.setMaximum(max);
   	    progressBar.setVisible(true);
    }
    public void setValue(int value)
    {
    	progressBar.setValue(value);
    }
    public void hide()
    {
    	 f.dispatchEvent(new WindowEvent(f, WindowEvent.WINDOW_CLOSING));
    }
    private int start;
    private int min;
    private int max;
    private String text;
    private String title;
    private JProgressBar progressBar;
    private JFrame f;
}
