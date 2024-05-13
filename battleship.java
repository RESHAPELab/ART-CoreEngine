/**
 * This file is from a project made back in High School. 
 * By Benjamin Carter
 * It represents a file from a game. This would be an example of an in-depth java program.
 */


package finalV;

import java.awt.event.KeyAdapter;
import java.net.URL;
import java.awt.event.KeyEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.net.InetAddress;
import java.net.MalformedURLException;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.ArrayList;
import java.util.Random;
import java.util.Scanner;
import java.util.Stack;

import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.sound.sampled.FloatControl;
import javax.sound.sampled.Line;
import javax.sound.sampled.Mixer;
import javax.sound.sampled.Port;
import javax.swing.JFrame;
import javax.swing.JOptionPane;


import sharedClasses.Numbers;

public class BattleshipRun 
{
	private static int keyDown;
	private static boolean close = false;
	private static boolean fin = false;
	private static Scanner input;
	private static PrintWriter output;
	private static ServerSocket server;
	private static Socket serverSocket;
	private static final int PORT  = 7891;
	// http://quartzhillhighschoolband.wikispaces.com/file/view/Fantasmic.MP3
	public static synchronized void playSound(final String url) {
		
		  new Thread(new Runnable() {
		  // The wrapper thread is unnecessary, unless it blocks on the
		  // Clip finishing; see comments.
		    public void run() {
		      try {
		        Clip clip = AudioSystem.getClip();
				AudioInputStream inputStream = AudioSystem.getAudioInputStream(this.getClass().getResource(url));
		        clip.open(inputStream);
		        clip.start(); 
		      } catch (Exception e) {
		        System.err.println(e.getMessage());
		      }
		    }
		  }).start();
		}
	public static synchronized void playSoundWithVolume(final String url, double volume) {
		
		  new Thread(new Runnable() {
		  // The wrapper thread is unnecessary, unless it blocks on the
		  // Clip finishing; see comments.
		    public void run() {
		      try {
		        Clip clip = AudioSystem.getClip();
				AudioInputStream inputStream = AudioSystem.getAudioInputStream(this.getClass().getResource(url));
		        clip.open(inputStream);
		        
		        FloatControl volCtrl = (FloatControl) clip.getControl(FloatControl.Type.MASTER_GAIN);
		        volCtrl.setValue((float)volume);
		        clip.start();
		         
		        
		      } catch (Exception e) {
		        System.err.println(e.getMessage());
		      }
		    }
		  }).start();
	}
		
	private static WindowAdapter closeWindow = new WindowAdapter() {
        public void windowClosing(WindowEvent e) {
            e.getWindow().dispose();
            close = true;
            input.close();
            output.println("E");
            output.println("E");
            output.flush();
            output.close();
            try {
				serverSocket.close();
			} catch (IOException e2) {
				// TODO Auto-generated catch block
				e2.printStackTrace();
			}
            catch(NullPointerException e2)
            {
            	
            }
            try {
				server.close();
			} catch (IOException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			}
            catch(NullPointerException e2)
            {
            	
            }
            System.exit(0);
        }
	};
	public static void runBackgroundMusic()
	{
		new Thread(new Runnable() {
			  // The wrapper thread is unnecessary, unless it blocks on the
			  // Clip finishing; see comments.
			    public void run() {
			    	while(true)
			    	{
			    		playSoundWithVolume("title.wav",-40);
					      try {
								Thread.sleep(90 * 1000);
							} catch (InterruptedException e) {
								// TODO Auto-generated catch block
								e.printStackTrace();
							}
					      playSoundWithVolume("background.wav",-40);
					      try {
							Thread.sleep(245 * 1000);
						} catch (InterruptedException e) {
							// TODO Auto-generated catch block
							e.printStackTrace();
						}
					      
			    	}
			    }
			  }).start();
	}
	
    public static void main(String[ ] args) throws InterruptedException
    {
    	    runBackgroundMusic();
    	    fin = false;
    	    MenuFrame menu = new MenuFrame();
    	    JFrame menuF  = new JFrame();
    	    menu.show(menuF);
    	    
    	    while(menu.getEvent() == 0)
    	    {
    	    	Thread.sleep(10);
    	    }
    	    //System.out.println(menu.getEvent());
    	   // menu.hide();
    	    fin = true;
    	    menuF.dispose();
    	    String ip;
    	    input = null;
			output = null;
    	    if(menu.getEvent() == 1)
    	    {
			try {
				ip = InetAddress.getLocalHost().getHostAddress();
				EasyProgressBar ipBox = new EasyProgressBar("Battleship!!","Waiting for player: IP: " + ip, 0,0,100);
				   ipBox.show();
				   //Thread.sleep(5000);
				   server =  new ServerSocket(PORT);
				   serverSocket = server.accept();
				   
				   input = new Scanner(serverSocket.getInputStream());
				   output = new PrintWriter(serverSocket.getOutputStream());
				   
				   
				   ipBox.hide();
			} catch (IOException e1) {
				// TODO Auto-generated catch block
				System.out.println("Not connected!");
				JOptionPane.showMessageDialog(null, "Not Connected! Press OK to quit");
				Thread.sleep(1000);
				try {
				input.close();
	            output.println("Exit");
	            output.close();
				}
				catch( NullPointerException ew)
				{
					
				}
	            try {
	            	try {
					serverSocket.close();
	            	}
	            	catch(NullPointerException e5 )
	            	{
	            		
	            	}
					} catch (IOException e) {
						// TODO Auto-generated catch block
					}
	            try {
					server.close();
				} catch (IOException e2) {
					// TODO Auto-generated catch block
				}
				 catch (NullPointerException e2) {
					// TODO Auto-generated catch block
				}
	            System.out.println("Out!");
				System.exit(0);
			}
    	    }
    	    if(menu.getEvent() == 2)
    	    {
				//EasyProgressBar ipBox = new EasyProgressBar("Battleship!!","Waiting for player: IP: " + ip, 0,0,100);
				   //ipBox.show();
				   ip = JOptionPane.showInputDialog("IP ADDRESS: ");
				   if(ip == null)
				   {
					   JOptionPane.showMessageDialog(null, "Canceled");
					   Thread.sleep(1000);
					   try
					   {input.close();
			            output.println("Exit");
			            output.close();
					   }
					   catch(NullPointerException ew)
					   {
						   
					   }
			            try {
			            	
							server.close();
						} catch (IOException e1) {
							// TODO Auto-generated catch block
							e1.printStackTrace();
						}
			            catch(NullPointerException er)
			            {
			            	
			            }
			            System.out.println("Quit!");
					   System.exit(0);
				   }
				  // Thread.sleep(1000);
				   //ServerSocket server =  new ServerSocket(7890);
				   try {
					 serverSocket = new Socket(ip,PORT);
					input = new Scanner(serverSocket.getInputStream());
					   output = new PrintWriter(serverSocket.getOutputStream());
				} catch (UnknownHostException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
					JOptionPane.showMessageDialog(null, "Can't Reach ip! Press OK to quit");
					Thread.sleep(1000);
					try {
						input.close();
			            output.println("Exit");
			            output.close();
					}
					catch (NullPointerException e1) {
						// TODO Auto-generated catch block
						
					}
		            try {
						serverSocket.close();
					} catch (IOException e2) {
						// TODO Auto-generated catch block
						e2.printStackTrace();
					}
		            try {
						server.close();
					} catch (IOException e1) {
						// TODO Auto-generated catch block
					}
		            catch (NullPointerException e1) {
						// TODO Auto-generated catch block
					}
		            System.out.println("Quit!");
					   System.exit(0);
				} catch (IOException e) {
					// TODO Auto-generated catch block
					JOptionPane.showMessageDialog(null, "Can't Reach ip!  - IO error - Press OK to quit");
					Thread.sleep(1000);
					try {
						input.close();
			            output.println("Exit");
			            output.close();
					}
					catch (NullPointerException e1) {
						// TODO Auto-generated catch block
						
					}
		            try {
						server.close();
					} catch (IOException e1) {
						// TODO Auto-generated catch block
						
					}
		            catch (NullPointerException e1) {
						// TODO Auto-generated catch block
						
					}
		            System.out.println("Exit");
					   System.exit(0);
				}
				   
				   
    	    }
    	    System.out.println("Connected!");
    	    
    	    output.println("A");
    	    output.flush();
    	    while(!input.hasNext())
		    {
		    	
		    }
		    input.next();
		    System.out.println("Got input");
    	   int mode = menu.getEvent();
    	   JFrame sframe = new JFrame();   /// Boat selection
		   sframe.setSize(800,480);
		   runBackgroundMusic();
		   if(mode == 1)
		   {
		   sframe.setTitle("Battleship - Place boats! - Host");
		   }
		   else
		   {
			   sframe.setTitle("Battleship - Place boats! - Cilent");
		   }
		   //sframe.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		   sframe.addWindowListener(closeWindow);
		   SelectorDraw sdrawer = new SelectorDraw();
		   sframe.getContentPane().add(sdrawer);
		   sframe.setVisible(true);
		   
		   ArrayList<Ship> ships = new ArrayList<Ship>();
		   ships.add(new Ship(0,0,2,false) );
		   ships.add(new Ship(0,2,3,false) );
		   ships.add(new Ship(0,4,4,false) );
		   ships.add(new Ship(0,6,5,false) );
		   ships.add(new Ship(0,8,3,false) );
		   
		   
		   Grid users = new Grid();

			for(Ship s : ships)
			{
				users.addShip(s);
			}
			sdrawer.setDataUser(users);
			sdrawer.reDraw();
		    keyDown = 0;
		    Stack<Integer> keys = new Stack<Integer>();
			sframe.addKeyListener(new KeyAdapter()
					{
				public void keyPressed(KeyEvent ke) {
                      //moveIt(evt);
					 if(ke.getKeyCode() == KeyEvent.VK_DOWN)
                     {
                     //System.out.println("Down!");
                     keyDown = 2;
                     keys.push(2);
                     }
	                 if(ke.getKeyCode() == KeyEvent.VK_UP)
	                 {
	                	 keyDown = 1;
	                	 keys.push(1);
	                	//System.out.println(keyDown);
	                 }
	                 if(ke.getKeyCode() == KeyEvent.VK_LEFT)
	                     {
	                	 //System.out.println("Left");
	                	 keyDown = 3;
	                	 keys.push(3);
	                 }
	                 if(ke.getKeyCode() == KeyEvent.VK_RIGHT)
	                     {
	                	 //System.out.println("Right!");
	                	 keyDown = 4;
	                	 keys.push(4);
	                 }

					}
					});
			double wx = 0;
			double wy = 0;
			int index = 0;
			while(true)
			{
				boolean clickFlag = !sdrawer.getClick();
		       while(clickFlag)
		       {
                 Thread.sleep(10);
                 if(!keys.isEmpty())
                 {
                	 //System.out.println("e");
                	 break;
                 }
                 clickFlag = !sdrawer.getClick();
		       }
		       //System.out.println("J");
		       if(!clickFlag)
		       {
		    	   wx = sdrawer.getCurrentX();
		    	   wy = sdrawer.getCurrentY();
		    	 //  System.out.println("Click");
		    	   //System.out.println(wx);
		    	   //System.out.println(wy);
		    	   //System.out.println("a");
		    	   if( (wx > 6) && (wx < 10) && (wy > 1) && (wy < 5))
			   	    {
		    		    ArrayList<Ship> shipsN = (ArrayList<Ship>) ships.clone(); 
		    		    
		    		    int i = 0;
		 	    	    double ux = Numbers.map(wx, 6, 10, 0, 10);
		 	    	    double uy = Numbers.map(wy, 1, 5, 10, 0);
		 	    	    //System.out.println((int)ux);
		 	    	    //System.out.println((int)uy);
		 	    	    
			   	    	for(Ship s : ships)
			   	    	{
							//System.out.println("X: " + s.getX() + " Y: " + s.getY());
			   	    		if((int)ux == s.getX()  && (int)  uy == s.getY())
			   	    		{
			   	    			index = i;
			   	    			//System.out.println("Ships: " + index);
			   	    			shipsN.remove(index);
			   	    			Grid usersN = new Grid();
			   	    			for(Ship s2 : shipsN)
								{
									usersN.addShip(s2);
								}
			   	    			int[][] arrayWithoutShip = usersN.getData();
			   	    			s.clearError();
			   	    			s.setDir(!s.getDir());
			   	    			
			   	    			
			   	    			if(s.shipCrossing(arrayWithoutShip) || s.getError())
			   	    			{
			   	    				playSound("test.wav");
			   	    				s.setDir(!s.getDir());
			   	    			}
			   	    			s.clearError();	
			   	    			ships.set(i,s.clone());
			   	    			
			   	    		}
			   	    		i++;
			   	    	}
			   	    	
	                    Grid newData = new Grid();
						for(Ship s : ships)
						{
							newData.addShip(s);
						}                    
						sdrawer.setDataUser(newData);
						sdrawer.reDraw();
						
			   	    }
		    	   if( (wx > .5) && (wx < 2.5) && (wy > .5) && (wy < 1.5))
			   	    {
		    	    // click outside box
		    	   //win.xPixelD(.5), win.yPixelD(1.5), win.xLengthD(2), win.yLengthD(1)
		    		   //System.out.println("Submit!");
		    		   break;
			   	    }
		       }
		       else if(!keys.isEmpty())
		       {
		    	   int key = keys.pop();
		    	   //keyDown = 0;
		    	   
		    	   
		    	   if( (wx > 6) && (wx < 10) && (wy > 1) && (wy < 5))
			   	    {
		    		    ArrayList<Ship> shipsN = (ArrayList<Ship>) ships.clone(); 
		    		    int i = 0;
		    		    
		 	    	    double ux = Numbers.map(wx, 6, 10, 0, 10);
		 	    	    double uy = Numbers.map(wy, 1, 5, 10, 0);
		 	    	    //System.out.println((int)ux);
		 	    	    //System.out.println((int)uy);
		 	    	    if(i != index)
		 	    	    {
		 	    	    	i = index;
		 	    	    }
			   	    	Ship si =  ships.get(i);
							//System.out.println("X: " + s.getX() + " Y: " + s.getY());
			   	    		if((int) ux == si.getX()  && (int) uy == si.getY())
			   	    		{
			   	    			//System.out.println("Ships: " + i);
			   	    			shipsN.remove(i);
			   	    			Grid usersN = new Grid();
			   	    			for(Ship s2 : shipsN)
								{
									usersN.addShip(s2);
								}
			   	    			int[][] arrayWithoutShip = usersN.getData();
			   	    			si.clearError();
			   	    			
			   	    			
			   	    		   if(key == 1)
			 		    	   {
			 		    		   si.setY(si.getY() - 1);
			 		    		   uy = uy - 1;
			 		    	   }
			 		    	   if(key == 2)
			 		    	   {
			 		    		  si.setY(si.getY() + 1);
			 		    		 uy = uy + 1;
			 		    	   }
			 		    	   if(key == 3)
			 		    	   {
			 		    		   si.setX(si.getX() - 1);
			 		    		  ux = ux - 1;
			 		    	   }
			 		    	   if(key == 4)
			 		    	   {
			 		    		  si.setX(si.getX() + 1);
			 		    		 ux = ux + 1;
			 		    	   }
			 		    	   //int y = s.getY()
			 		    	   //System.out.println("New: " + si.getX() + ", Y: " + si.getY() );
			   	    			
			   	    			if(si.shipCrossing(arrayWithoutShip) || si.getError())
			   	    			{
			   	    				playSound("test.wav");
			   	    				if(key == 1)               // reset to previous
					 		    	   {
					 		    		   si.setY(si.getY() + 1);
					 		    		  uy = uy + 1;
					 		    	   }
					 		    	   if(key == 2)
					 		    	   {
					 		    		  si.setY(si.getY() - 1);
					 		    		 uy = uy - 1;
					 		    	   }
					 		    	   if(key == 3)
					 		    	   {
					 		    		   si.setX(si.getX() + 1);
					 		    		  ux = ux + 1;
					 		    	   }
					 		    	   if(key == 4)
					 		    	   {
					 		    		  si.setX(si.getX() - 1);
					 		    		 ux = ux - 1;
					 		    	   }
			   	    			}
			   	    			
			   	    			si.clearError();	
			   	    			ships.set(i,si.clone());
			   	    			wx = Numbers.map(ux, 0, 10, 6, 10);
				 	    	    wy = Numbers.map(uy, 10, 0, 1, 5);
			   	    	}
			   	    	
	                    Grid newData = new Grid();
						for(Ship s : ships)
						{
							newData.addShip(s);
						}                    
						sdrawer.setDataUser(newData);
						sdrawer.reDraw();
						
			   	    }
		       } 
		       
			}
		    sframe.removeKeyListener(null);
		    sframe.dispose();
		    //System.out.println("Closed!");
		    output.println("sd");
		    output.flush();
		    EasyProgressBar alert = new EasyProgressBar("Battleship!", "Waiting for opponent... Code: 12", 0,0,100);
		    alert.show();
		    while(!input.hasNext())
		    {
		    	
		    }
		     input.next();
		    
		    
		    alert.hide();
		    // transfer data after both are done.
		    alert = new EasyProgressBar("Battleship!", "Transfering...",0,0,200);
		    alert.show();
		    int i = 0;
		    ArrayList<Ship> userShips = (ArrayList<Ship>) ships.clone(); 
			Grid userGrid = new Grid();
			for(Ship s: userShips)
			{
				userGrid.addShip(s);
			}
			int[][] userData = userGrid.getData();  // output user ship data
			int chksum = 0;
			for(int y = 0; y < 10; y++)
			{
				for(int x = 0; x < 10; x++)
				{
					output.println(userData[y][x]);
					i = i + 1;
					chksum = chksum + userData[y][x];
					alert.setValue(i);
				}
			}
			
			output.println(chksum);
			output.flush();                          
			while(!input.hasNext())                      // wait for input
			{
				
			}
			//101 different tokens.
			int counterX = 0;
			int counterY = 0;
			int[][] opponentData = {
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0},
					{ 0,0,0,0,0,0,0,0,0,0}
			};
			
			int sum = 0;
			int ck = 0;
			int iCount = 0;
			while(input.hasNext())
			{
				int in = Integer.parseInt(input.next());
				opponentData[counterY][counterX] = in;
				ck = ck + in;
				counterX++;
				if(counterX == 10)
				{
					counterX = 0;
					counterY++;
				}
				if(counterY == 10)
				{
					break;
				}
				alert.setValue(iCount + 100);
				iCount++;
			}
			sum = Integer.parseInt(input.next());
			System.out.println(sum == ck);
			if(sum != ck)
			{
				JOptionPane.showMessageDialog(null, "Ckecksum failed! - Press OK to quit");
				input.close();
	            output.println("E");
	            output.flush();
	            output.close();
	            try {
					serverSocket.close();
				} catch (IOException e2) {
					// TODO Auto-generated catch block
					e2.printStackTrace();
				}
	            catch(NullPointerException e2)
	            {
	            	
	            }
	            try {
					server.close();
				} catch (IOException e1) {
					// TODO Auto-generated catch block
					e1.printStackTrace();
				}
	            catch(NullPointerException e2)
	            {
	            	
	            }
	            System.exit(0);
			}
			Grid oppGrid = new Grid(true);
			oppGrid.setData(opponentData);
			oppGrid.printGrid();
			alert.hide();
		   JFrame frame = new JFrame();
		   frame.setSize(800,480);
		   if(mode == 1)
		   {
			   frame.setTitle("Battle Ship - Host");
		   }
		   if(mode == 2)
		   {
			   frame.setTitle("Battle Ship! - Cilent");
		   }
		   
		   //frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		   frame.addWindowListener(closeWindow);
		   MainDraw drawer = new MainDraw();
		   frame.getContentPane().add(drawer);
		   frame.setVisible(true);
		   
		   Grid guessGrid = new Grid(true);
		   drawer.setDataGuess(guessGrid);
		   drawer.setDataUser(userGrid); 
		   drawer.reDraw();
		   drawer.setEdibleUserGrid(false);
		   drawer.setEdibleGuessGrid(true);
		   drawer.reDraw();
		   
		   boolean plr = false;
		   plr = (mode == 1);
		   output.println("H");
		   output.flush();
		  while(!input.hasNext())
		   {
		   
		   }
		  input.next();
		   Thread.sleep(10);
		   plr = (mode == 1);
		   /*if(mode == 1)
		   {
			   Random r = new Random();
			   boolean coin = r.nextBoolean();
			   if(coin)
			   {
			   output.println(1);
			   System.out.println("1 - Host");
			   plr = true;
			   }
			   else
			   {
				   output.println(0);
				   System.out.println("0 - Host");
			   }
			   output.flush();
			   
		   }
		   if(mode == 2)
		   {
			   while(!input.hasNext())
			   {
				   
			   }
			   String s = input.next();
			   System.out.println(s);
			   if(s.equals("1"))
			   {
				   plr = true;
			   }
			   else
			   {
				   plr = false;
			   }
			   
		   }*/
		   /*
		   while(input.hasNext())
		   {
			   input.next();
		   }
		  
		   //ArrayList<Ship> oppShips = (ArrayList<Ship>) ships.clone();
		   /*
		   ArrayList<Ship> oppShips = new ArrayList<Ship>();
		   oppShips.add(new Ship(7,0,2,false));
		   oppShips.add(new Ship(6,2,3,false));
		   oppShips.add(new Ship(5,4,4,false));
		   oppShips.add(new Ship(5,7,5,false));
		   oppShips.add(new Ship(6,9,3,false));
		   */
		  // for(Ship s: oppShips)
		  // {
		//	   oppGrid.addShip(s);
		   //}
		   
		   
		   int opponentHit = 0;
		   int userHit = 0;
		   
		   if(plr)
		   {
			   //output.println("1");
			   //output.flush();
			   JOptionPane.showMessageDialog(null,"You Go first!");
			   drawer.setEdibleGuessGrid(true);
		   }
		   else
		   {
			   //output.println("0");
			   //output.flush();
			   JOptionPane.showMessageDialog(null,"Opponent Goes First!");
			   drawer.setEdibleGuessGrid(false);
			   /*while(!input.hasNext())
			   {
				   
			   }
			    if( 1 == Integer.parseInt(input.next()))
			    {
			    	JOptionPane.showMessageDialog(null,"Bad input!");
			    }
			    */
			   EasyProgressBar e = new EasyProgressBar("Battleship", "Wating for opponent...",0,0,100);
			   drawer.setEdibleGuessGrid(false);
			   e.show();
			   int oX = 0;// = Integer.parseInt(JOptionPane.showInputDialog("X: "));
			   int oY = 0;// = Integer.parseInt(JOptionPane.showInputDialog("Y: "));
			   
			   while(!input.hasNext())
			   {
				   
			   }
			   oX = Integer.parseInt(input.next());
			   oY = Integer.parseInt(input.next());
			   
			   e.hide();
			   
			   int[][] usr = userGrid.getData();
			   if(usr[oY][oX] == 1 || usr[oY][oX] == 2)
			   {
				   //System.out.println("Hit!");
				   
				   usr[oY][oX] = 7;
				   userGrid.setData(usr);
				   drawer.setDataUser(usr);
				   drawer.reDraw();
				   userHit++;
				   playSound("hit.wav");
			   }
			   else
			   {
				   //System.out.println("Miss");
				   usr[oY][oX] = 6;
				   userGrid.setData(usr);
				   drawer.setDataUser(usr);
				   drawer.reDraw();
				   playSound("splash.wav");
			   }
			   
			   drawer.setEdibleGuessGrid(true);
		   }
		   while(true)
		   {
			   
			   while(!drawer.getClick())
			   {
				   Thread.sleep(10);
			   }
			   
			   double currentX = drawer.getCurrentX();
			   double currentY = drawer.getCurrentY();
			   if( (currentX > 6) && (currentX < 10) && (currentY > 1) && (currentY < 5) )
			   {
				   boolean badGuess = false;
				   if(!drawer.getEdibleGuessGrid())
				   {
					   badGuess = true;
				   }
				   int mapX = (int) Numbers.map(currentX, 6, 10, 0, 10);
				   int mapY = (int) Numbers.map(currentY, 1, 5, 10, 0);
				   //System.out.println("Clicked: " + mapX + " , Y: " + mapY);
				   
				   int code = oppGrid.getData()[mapY][mapX];
				   if(code == 1 || code == 2)
				   {
					   int[][] x = guessGrid.getData();
					   if(x[mapY][mapX] == 5)
					   {
						   JOptionPane.showMessageDialog(null, "You already guessed there!");
						   badGuess = true;
						   playSound("test.wav");
					   }
					   else
					   {
						   playSound("hit.wav");
					   }
					   x[mapY][mapX] = 5;
					   guessGrid.setData(x);
					   opponentHit = opponentHit + 1;
					   
				   }
				   else
				   {
					   int[][] x = guessGrid.getData();
					   if(x[mapY][mapX] == 4)
					   {
						   JOptionPane.showMessageDialog(null, "You already guessed there!");
						   badGuess = true;
						   playSound("test.wav");
					   }
					   else
					   {
						   playSound("miss.wav");
					   }
					   x[mapY][mapX] = 4;
					   guessGrid.setData(x);
				   }
				   if(!badGuess)
				   {
					   drawer.setDataGuess(guessGrid);
					   drawer.reDraw();
					   //JOptionPane.showMessageDialog(null,"Wait");
					   output.println(mapX);
					   output.println(mapY);
					   output.flush();
					   if(opponentHit == 17)
					   {
						   playSound("test.wav");
						   JOptionPane.showMessageDialog(null,"YOU WIN!");
						   drawer.setEdibleGuessGrid(true);
						   while(true)
						   {
							   Thread.sleep(1000);
						   }
					   }
					   EasyProgressBar e = new EasyProgressBar("Battleship", "Wating for opponent...",0,0,100);
					   drawer.setEdibleGuessGrid(false);
					   e.show();
					   int oX = 0;// = Integer.parseInt(JOptionPane.showInputDialog("X: "));
					   int oY = 0;// = Integer.parseInt(JOptionPane.showInputDialog("Y: "));
					   
					   while(!input.hasNext())
					   {
						   if(userHit == 17)
						   {
							   playSound("test.wav");
							   JOptionPane.showMessageDialog(null,"You lost! Better luck next time!");
							   drawer.setEdibleGuessGrid(true);
							   int[][] guess = guessGrid.getData();
							   guessGrid.printGrid();
							   int[][] opp = oppGrid.getData();
							   for(int y = 0; y < 10; y++)
							   {
								   for(int x = 0; x < 10; x++)
								   {
									   if(guess[y][x] == 3)
									   {
										   guess[y][x] = opp[y][x];
									   }
								   } 
							   }
							   drawer.setDataGuess(guess);
							   while(true)
							   {
								   Thread.sleep(1000);
							   }
						   }
					   }
					   try
					   {
					   oX = Integer.parseInt(input.next());
					   oY = Integer.parseInt(input.next());
					   }
					   catch(Exception e4)
					   {
				    	   input.next().equals("E");
				    	   JOptionPane.showMessageDialog(null, "The opponent quit. Press OK to quit");
				    	   sframe.dispose();
				    	   input.close();
				            output.println("E");
				            output.close();
				            try {
								serverSocket.close();
							} catch (IOException e2) {
								// TODO Auto-generated catch block
								e2.printStackTrace();
							}
				            catch(NullPointerException e2)
				            {
				            	
				            }
				            try {
								server.close();
							} catch (IOException e1) {
								// TODO Auto-generated catch block
								e1.printStackTrace();
							}
				            catch(NullPointerException e2)
				            {
				            	
				            }
				            System.exit(0);
					   }
					   e.hide();
					   
					   int[][] usr = userGrid.getData();
					   if(usr[oY][oX] == 1 || usr[oY][oX] == 2)
					   {
						   System.out.println("Hit!");
						   
						   usr[oY][oX] = 7;
						   userGrid.setData(usr);
						   drawer.setDataUser(usr);
						   drawer.reDraw();
						   userHit++;
						   playSound("hit.wav");
					   }
					   else
					   {
						   System.out.println("Miss");
						   usr[oY][oX] = 6;
						   userGrid.setData(usr);
						   drawer.setDataUser(usr);
						   drawer.reDraw();
						   playSound("splash.wav");
					   }
					   System.out.println(userHit + " , " + opponentHit);
					   if(userHit == 17)
					   {
						   playSound("test.wav");
						   JOptionPane.showMessageDialog(null,"You lost! Better luck next time!");
						   drawer.setEdibleGuessGrid(true);
						   
						   int[][] guess = guessGrid.getData();
						   int[][] opp = oppGrid.getData();
						   guessGrid.printGrid();
						   for(int y = 0; y < 10; y++)
						   {
							   for(int x = 0; x < 10; x++)
							   {
								   if(guess[y][x] == 3)
								   {
									   guess[y][x] = opp[y][x];
								   }
							   } 
						   }
						   drawer.setDataGuess(guess);
						   while(true)
						   {
							   Thread.sleep(1000);
						   }
					   }
					   
					   drawer.setEdibleGuessGrid(true);
					   
					   // lets pertend that the opponent is you.
				}
				   
			   }
		   }
		   

    }
}

